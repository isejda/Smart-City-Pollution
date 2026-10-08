# diploma

Smart City Pollution - an air-quality monitoring platform: Vue 3 (Vite) frontend + Django REST Framework backend + Postgres, all run via Docker Compose.

The app has two halves:

- **Public portal** (`/`) - an open dashboard of live air-quality data (PM2.5, PM10, temperature, humidity, noise, UV…) across sensor nodes in Tiranë, Korçë and Elbasan: a map, trends, health advice. No login required - this data is public.
- **Monitoring console** (`/monitorimi`) - an operator/staff panel for node configuration and reports. Gated behind JWT authentication (sign in via the "Hyrje për stafin" button in the public portal's nav).

## Stack

- **Frontend**: Vue 3, Vite, Vue Router, Pinia, Axios, Leaflet - dev server on `:5174` (host). (Mapped off the default 5173 because another project on this machine already uses that port - change it back in `docker-compose.yml` if that's not the case for you.)
- **Backend**: Django 5 + Django REST Framework, JWT auth via `djangorestframework-simplejwt`, `django-filter`, on `:8000`.
- **Database**: Postgres 16.

## Getting started

```bash
cp .env.example .env   # already done if you're reading this after scaffolding
docker compose up --build
```

- Public portal: http://localhost:5174
- Monitoring console: http://localhost:5174/#/monitorimi (requires sign-in)
- Backend API: http://localhost:8000/api/
- Health check: http://localhost:8000/api/health/
- Django admin: http://localhost:8000/admin/

On first boot the backend runs migrations and seeds the database (`seed_data` management command) with sample cities, sensor nodes, a synthetic readings history and a superadmin account, so the app has data out of the box.

### Superadmin credentials

`seed_data` creates (or updates) a superadmin on every boot. Use it for both the Django admin (`/admin/`) and the monitoring console sign-in:

| Username | Password   | Email               |
|----------|------------|---------------------|
| `admin`  | `admin123` | `admin@example.com` |

They come from `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD` and `DJANGO_SUPERUSER_EMAIL` in `.env` (the values above are the defaults). The password is reset to that value on every seed, so change it via `.env`, not in the admin UI, and use a strong one outside local dev.

## Auth

Operator accounts are created via the register endpoint (there's no self-serve signup link in the UI - that's a deliberate choice, since only network operators should reach the console).

- `POST /api/register/` - public. Body: `{"username", "email", "password"}`.
- `POST /api/login/` - public. Body: `{"username", "password"}` → `{"access", "refresh"}`.
- `POST /api/login/refresh/` - public. Body: `{"refresh"}` → new `{"access"}`.

```bash
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "operator1", "email": "you@example.com", "password": "a-strong-password"}'

curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "operator1", "password": "a-strong-password"}'
```

The DRF default permission is `IsAuthenticated`. Within the `monitoring` app, the read-only public-data endpoints (parameters, cities, nodes, readings, snapshot, dataset, network-stats) explicitly set `permission_classes = [AllowAny]`; the operator-facing ones (runtime settings) are left on the authenticated default, since they can mutate server state. The one write on `readings` (device ingest, below) uses its own device key instead.

## Node data ingestion (webhook)

Physical nodes (Arduino / LoRaWAN webhook relay, Raspberry Pi) push live readings to:

```
POST /api/readings/
```

- **Auth**: header `X-Device-Key: <DEVICE_INGEST_KEY>` - a shared secret, not JWT (hardware can't do an interactive login). Set `DEVICE_INGEST_KEY` in `.env`; if it's unset the backend falls back to `dev-only-device-key-change-me`, so always set it outside local dev.
- **Body** (JSON): `eui` (required - the node's device EUI, must match a registered node), `ts` (required - ISO 8601 timestamp), and any of the raw sensor values `pm25`, `pm10`, `tmp`, `hum`, `snd`, `uv`, `pres`, `rain` (all optional).
- **Responses**: `201` with the stored reading; `400` if the EUI is unknown or a reading for that node at that `ts` already exists (safe to ignore on device retries); `403` if the key is missing or wrong.
- Each accepted reading triggers a background re-run of `generate_forecast` (skipped if one is already running).

```bash
curl -X POST http://localhost:8000/api/readings/ \
  -H "Content-Type: application/json" \
  -H "X-Device-Key: $DEVICE_INGEST_KEY" \
  -d '{"eui": "A8404172C75D105A", "ts": "2026-10-08T12:00:00Z", "pm25": 14.2, "pm10": 22.8, "tmp": 18.5, "hum": 61}'
```

## AI forecast (72h)

`backend/ml_forecast/` is a validated forecasting model (per-target seasonal/gradient-boosting
champions, trained and backtested on this network's real historical export) vendored in as a
plain, checksum-verified Python package - see its own report for methodology. On every backend
boot, `entrypoint.sh` runs, in order:

1. `seed_data` - synthetic config + readings for all 6 nodes (unchanged, as before).
2. `import_real_history` - replaces the synthetic readings of any node whose EUI matches a real
   device in `ml_forecast/data/sensor_hourly_clean.csv` with that real history, and moves the
   replay cursor to its last real hour. Currently matches 5 of 6 nodes (`ND-06` has no real
   counterpart in the training data and keeps its synthetic history).
3. `generate_forecast` - runs the trained model bundle against the current `Reading` history and
   (re)writes the `Forecast` table. Only sensor/target pairs that pass the model's own freshness +
   coverage gate get rows - at the real data's cutoff that is exactly node `ND-01`
   (`A8404172C75D105A`) for 7 of 8 targets (no pressure).

Forecast rows are folded into `/api/dataset/` per node (`forecastMeta` + `forecast.<field>`), so
the public portal's Trends panel and the node drawer show the model's actual 72h forecast - with
an "AI model" badge - wherever it exists, and fall back to the existing client-side heuristic
everywhere else. Re-run step 2+3 by hand after changing the data:

```bash
docker compose exec backend python manage.py import_real_history
docker compose exec backend python manage.py generate_forecast
```

## Project layout

```
backend/
  config/       Django project settings & root urls
  api/          register/login/refresh (JWT), health check
  monitoring/   air-quality domain: parameters, cities, nodes, readings, forecasts, settings
  ml_forecast/  vendored forecasting model (src/, artifacts/*.joblib, real historical CSV)
frontend/
  src/views/public/   the public portal (map, trends, advice)
  src/views/monitor/  the operator console (nodes, reports, settings)
  src/engine/         framework-agnostic "Air" engine the two portals share (replay clock, calibration, forecast)
docker-compose.yml
.env.example
```

## Local dev without Docker (optional)

Backend:
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```
