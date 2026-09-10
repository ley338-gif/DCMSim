# Entwicklung

## Repository-Struktur

`apps/api` enthält FastAPI, SQLAlchemy, Alembic und DICOM-Domänenlogik. `apps/web` enthält React/Vite. `e2e` enthält Browser-Flows, `docs` die Betriebs- und Architekturunterlagen.

Im Frontend liegen generische Komponenten unter `src/components/ui`, Shell-Komponenten unter `src/components/layout` und wiederverwendbare DICOM-Komponenten unter `src/components/dicom`. Zentrale Tokens befinden sich in `src/theme/tokens.css`. Die interne Komponentenübersicht ist lokal unter `/dev/ui` erreichbar und gehört nicht zur Hauptnavigation.

## Lokal starten

Python 3.12: `python -m pip install -e ".[dev]"`, danach `alembic -c apps/api/alembic.ini upgrade head` und `uvicorn app.main:app --app-dir apps/api --reload`. Frontend: in `apps/web` erst `npm install`, dann `npm run dev`. Docker: `docker compose up --build`.

## Migrationen

Anwenden: `alembic -c apps/api/alembic.ini upgrade head`. Erstellen: `alembic -c apps/api/alembic.ini revision --autogenerate -m "kurze beschreibung"`. Die generierte Migration prüfen und gegen eine leere SQLite-Datei testen.

## Qualitätsprüfungen

- Backend-Lint: `ruff check apps/api`
- Backend-Tests: `pytest` oder getrennt `pytest apps/api/tests/unit`, `integration`, `dicom`
- Frontend: `npm run lint`, `npm run typecheck`, `npm test -- --run`, `npm run build`
- E2E: `npx playwright install chromium`, danach `npm run e2e`

Lokale Test-SCPs werden in den DICOM-Tests mit pynetdicom auf dynamisch freien Localhost-Ports gestartet. Docker nutzt dasselbe Image wie die Produktion und ein Volume unter `/data`.

## Release-Prozess

Version und Changelog aktualisieren; Backend-, Frontend-, E2E-, Migration- und Docker-Prüfungen ausführen; DICOM Support Matrix und User Manual abgleichen; anschließend Tag gemäß Semantic Versioning erstellen.
