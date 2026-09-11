# DCMSim

DCMSim ist ein vollständig lokales Diagnosewerkzeug für PACS-, RIS- und Medizintechnik-Administratoren. Es simuliert eine Modalität und prüft Modality Worklist (C-FIND), PACS Storage (C-STORE) und Connectivity (C-ECHO). Technische Antworten, ausgehandelte DICOM-Parameter und Statuscodes bleiben sichtbar und werden lokal protokolliert.

## Funktionen in 0.2.1

- MWL C-FIND mit gezielten Filtern oder Broad Query, Ergebnis-Dataset und Nulltreffer-Diagnose
- C-STORE mit synthetischem Testbild oder flüchtig verarbeiteter `.dcm`-Datei
- sechs Storage SOP Classes, Explicit und Implicit VR Little Endian
- gespeicherte Ziele, C-ECHO und lokale SQLite-Testhistorie
- stabile Fehlercodes für Verbindung, Association, Timeout und Presentation Context
- Modalitätsprofile, die getrennte MWL- und Store-Ziele referenzieren
- manueller kombinierter Modalitätscheck mit Worklist-, Store- und Gesamtergebnis
- diagnostische MWL-Wiederholung ohne Station AE bei null Treffern
- synthetische, SOP-spezifische Testobjekte für SC, CT, MR, US, CR und DX
- direkte Wiederholung und abbrechbare Browseranzeige für Modalitätschecks
- konkrete nächste Schritte zu klassifizierten DICOM-Fehlern
- JSON-Konfigurationsexport/-import, konsistentes SQLite-Backup und manuelle History-Retention

## Start mit Docker

Voraussetzung ist Docker mit Compose. Danach:

```bash
docker compose up --build
```

DCMSim ist unter `http://localhost:8080` erreichbar. Die Datenbank liegt im Volume unter `/data/dcmsim.db`.

## Lokale Entwicklung

Erforderlich sind Python 3.12 und Node.js 22.

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
alembic -c apps/api/alembic.ini upgrade head
uvicorn app.main:app --app-dir apps/api --reload

cd apps/web
npm install
npm run dev
```

Konfiguration erfolgt über die Variablen aus `.env.example`. Backend-Tests: `pytest`; Backend-Lint: `ruff check apps/api`; Frontend-Prüfung: `npm run lint && npm run typecheck && npm test -- --run && npm run build`. Der Standard-Datenpfad im Container ist `/data/dcmsim.db`.

Unterstützt werden C-ECHO SCU, MWL C-FIND SCU und C-STORE SCU. Für den schnellsten Systemcheck zuerst unter **Ziele** ein System und anschließend unter **Modalitäten** ein Geräteprofil anlegen. Details stehen in der [DICOM Support Matrix](docs/dicom-support.md). Bedienung: [User Manual](docs/user-manual.md). Fehleranalyse: [Troubleshooting](docs/troubleshooting.md).

> DCMSim hat im MVP keine Authentifizierung und ist ausschließlich für vertrauenswürdige interne Netze gedacht. Uploads können Patientendaten enthalten und werden nicht dauerhaft gespeichert. Es gibt keine Telemetrie oder Cloud-Kommunikation.
