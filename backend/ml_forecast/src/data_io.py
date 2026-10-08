"""Memory-efficient input/output utilities for the supplied XLSX dataset.

The source workbook stores almost 300k rows in one worksheet and keeps dates
and identifiers in ``sharedStrings.xml``.  A streaming parser avoids loading
the full 100+ MB worksheet XML tree into memory and preserves empty cells.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Iterable, Iterator, Sequence
from xml.etree import ElementTree as ET


MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"

MODEL_CODE_PATHS = (
    "src/__init__.py",
    "src/data_io.py",
    "src/features.py",
    "src/forecasting.py",
    "src/metrics.py",
    "src/modeling.py",
    "src/preprocessing.py",
    "scripts/extract_data.py",
    "scripts/predict.py",
    "scripts/train_model.py",
)


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Return a stable SHA-256 checksum for an input or artifact."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_mapping_sha256(value: dict) -> str:
    """Hash a configuration by meaning rather than YAML whitespace or comments."""

    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def model_code_tree_sha256(project_root: str | Path) -> str:
    """Hash the exact training/serving Python surface with stable path framing."""

    project_root = Path(project_root)
    digest = hashlib.sha256()
    for relative in MODEL_CODE_PATHS:
        path = project_root / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Model code identity file is missing or unsafe: {relative}")
        encoded_name = relative.encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(encoded_name).to_bytes(4, "big"))
        digest.update(encoded_name)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def spreadsheet_safe_text(value):
    """Neutralize strings that spreadsheet applications may execute as formulas."""

    if not isinstance(value, str):
        return value
    candidate = value.lstrip()
    if candidate.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def spreadsheet_safe_frame(frame):
    """Return a copy with every string cell made safe for CSV/XLSX export."""

    safe = frame.copy()
    for column in safe.columns:
        if safe[column].dtype == object or str(safe[column].dtype).startswith("string"):
            safe[column] = safe[column].map(spreadsheet_safe_text)
    return safe


def write_csv_safe(frame, path: str | Path, **kwargs) -> None:
    """Write a presentation/output CSV with formula-like text neutralized."""

    spreadsheet_safe_frame(frame).to_csv(path, **kwargs)


def _load_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    strings: list[str] = []
    if "xl/sharedStrings.xml" not in archive.namelist():
        return strings
    with archive.open("xl/sharedStrings.xml") as handle:
        for event, element in ET.iterparse(handle, events=("end",)):
            if element.tag == f"{MAIN_NS}si":
                strings.append("".join(node.text or "" for node in element.iter(f"{MAIN_NS}t")))
                element.clear()
    return strings


def _first_worksheet_path(archive: zipfile.ZipFile) -> tuple[str, str]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    sheets = workbook.find(f"{MAIN_NS}sheets")
    if sheets is None or not list(sheets):
        raise ValueError("The workbook does not contain a worksheet.")
    first_sheet = list(sheets)[0]
    sheet_name = first_sheet.attrib.get("name", "Sheet1")
    relationship_id = first_sheet.attrib.get(f"{REL_NS}id")
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    for relationship in relationships:
        if relationship.attrib.get("Id") == relationship_id:
            target = relationship.attrib["Target"].lstrip("/")
            if not target.startswith("xl/"):
                target = f"xl/{target}"
            return sheet_name, target
    raise ValueError("Could not resolve the first worksheet relationship.")


def _column_index(cell_reference: str | None, fallback: int) -> int:
    if not cell_reference:
        return fallback
    match = re.match(r"([A-Z]+)", cell_reference.upper())
    if not match:
        return fallback
    index = 0
    for char in match.group(1):
        index = index * 26 + (ord(char) - 64)
    return index - 1


def _decode_cell(cell: ET.Element, shared_strings: Sequence[str]):
    cell_type = cell.attrib.get("t")
    value_element = cell.find(f"{MAIN_NS}v")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{MAIN_NS}t"))
    if value_element is None or value_element.text is None:
        return None
    raw = value_element.text
    if cell_type == "s":
        return shared_strings[int(raw)]
    if cell_type == "b":
        return raw == "1"
    if cell_type in {"str", "e"}:
        return raw
    try:
        number = float(raw)
        return int(number) if number.is_integer() else number
    except ValueError:
        return raw


def iter_first_sheet_rows(path: str | Path) -> tuple[str, Iterator[list]]:
    """Return the first sheet name and a streaming iterator over row values."""

    archive = zipfile.ZipFile(path)
    shared_strings = _load_shared_strings(archive)
    sheet_name, worksheet_path = _first_worksheet_path(archive)

    def _rows() -> Iterator[list]:
        try:
            with archive.open(worksheet_path) as handle:
                for event, element in ET.iterparse(handle, events=("end",)):
                    if element.tag != f"{MAIN_NS}row":
                        continue
                    values: list = []
                    fallback_index = 0
                    for cell in element.findall(f"{MAIN_NS}c"):
                        index = _column_index(cell.attrib.get("r"), fallback_index)
                        if index >= len(values):
                            values.extend([None] * (index - len(values) + 1))
                        values[index] = _decode_cell(cell, shared_strings)
                        fallback_index = index + 1
                    yield values
                    element.clear()
        finally:
            archive.close()

    return sheet_name, _rows()


def xlsx_to_csv(
    input_path: str | Path,
    output_path: str | Path,
    expected_columns: int | None = None,
    expected_header: Sequence[str] | None = None,
) -> dict:
    """Stream the first XLSX worksheet to UTF-8 CSV and return extraction metadata."""

    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet_name, rows = iter_first_sheet_rows(input_path)
    row_count = 0
    header: list[str] | None = None
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        for row in rows:
            if header is None:
                header = [str(value) if value is not None else "" for value in row]
                if expected_columns is not None and len(header) != expected_columns:
                    raise ValueError(
                        f"Expected {expected_columns} columns, found {len(header)}: {header}"
                    )
                if expected_header is not None and header != list(expected_header):
                    raise ValueError(
                        "Workbook schema mismatch. Expected columns in this exact order: "
                        f"{list(expected_header)}; found: {header}"
                    )
                writer.writerow(header)
                continue
            if len(row) < len(header):
                row.extend([None] * (len(header) - len(row)))
            writer.writerow(row[: len(header)])
            row_count += 1
    metadata = {
        "source_file": input_path.name,
        "source_sha256": sha256_file(input_path),
        "sheet_name": sheet_name,
        "rows": row_count,
        "columns": len(header or []),
        "column_names": header or [],
        "csv_file": output_path.name,
        "csv_sha256": sha256_file(output_path),
    }
    return metadata


def write_json(path: str | Path, payload) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
