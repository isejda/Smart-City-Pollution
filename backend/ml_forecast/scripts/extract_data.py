#!/usr/bin/env python3
"""Extract the first worksheet from the provided XLSX into a training CSV."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_io import write_json, xlsx_to_csv
from src.preprocessing import load_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to the source XLSX file")
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "data" / "processed" / "sensor_readings.csv"),
        help="Destination CSV path",
    )
    parser.add_argument(
        "--metadata",
        default=str(PROJECT_ROOT / "data" / "processed" / "extraction_metadata.json"),
        help="Destination extraction metadata JSON",
    )
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "config" / "model_config.yaml"),
        help="Schema and modeling configuration",
    )
    args = parser.parse_args()
    config = load_config(args.config)
    metadata = xlsx_to_csv(
        args.input,
        args.output,
        expected_columns=int(config["data"]["expected_columns"]),
        expected_header=config["data"]["source_columns"],
    )
    write_json(args.metadata, metadata)
    print(f"Extracted {metadata['rows']:,} rows from {metadata['sheet_name']} to {args.output}")


if __name__ == "__main__":
    main()
