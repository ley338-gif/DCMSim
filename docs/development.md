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
- Full Stack: `npm run e2e:full-stack` startet FastAPI, temporäres SQLite, React sowie lokale MWL-, Study-Root- und Storage-SCPs

Lokale Test-SCPs werden in den DICOM-Integrationstests mit pynetdicom auf dynamisch freien Localhost-Ports gestartet. Der Full-Stack-Harness verwendet feste, nur lokal gebundene Testports und eine temporäre Datenbank. Alle Daten sind synthetisch. Docker nutzt dasselbe Image wie die Produktion und ein Volume unter `/data`.

Der Docker-CI-Job startet zusätzlich einen kurzlebigen Verification-SCP in einem getrennten Container auf einem privaten Testnetz. Der Anwendungscontainer sendet per API einen echten C-ECHO dorthin. Nur der HTTP-Testport wird an Host-Loopback veröffentlicht; der DICOM-Testport bleibt innerhalb des Docker-Netzes.

`DCMSIM_LOG_LEVEL` steuert die DCMSim-Anwendungslogs. Die Bibliothekslogger von pydicom und pynetdicom bleiben aus Datenschutzgründen mindestens auf `WARNING`; ausführliche DICOM-Antworten werden kontrolliert im aktuellen Browser statt im Container-Log dargestellt.

## Release-Prozess

Version und Changelog aktualisieren; Backend-, Frontend-, E2E-, Migration- und Docker-Prüfungen ausführen; DICOM Support Matrix und User Manual abgleichen; anschließend Tag gemäß Semantic Versioning erstellen. Vor einem Upgrade empfiehlt sich ein SQLite-Backup über **Einstellungen → Datensicherung**.
