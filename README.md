# DCMSim

DCMSim ist ein vollständig lokales Diagnosewerkzeug für PACS-, RIS- und Medizintechnik-Administratoren. Es prüft Modality Worklist, PACS-Studienabfragen, Storage und Connectivity per DICOM. Technische Antworten, ausgehandelte Parameter und Statuscodes bleiben sichtbar und werden lokal protokolliert.

## Funktionen in 0.3.9

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
- sichere PACS-Studienabfrage per Study Root C-FIND mit DICOM-Detailansicht
- eigene Query/Retrieve-Konfiguration je Ziel; Patientenergebnisse werden nicht in der Historie gespeichert
- vollständige Dashboard-Integration für PACS-Suche, Query/Retrieve-Ziele und Modalitätsprüfungen
- datensparsame Testhistorie ohne Worklist-/PACS-Trefferlisten, Suchfilter, Patientenname oder Patient-ID
- datensparsame Container-Logs ohne automatische pydicom-/pynetdicom-Dataset-Dumps
- serverseitig filterbare und paginierte Testhistorie mit datensparsamem CSV-Export
- wirksame lokale Benutzerstandards für Calling AE und kompakte Tabellen
- evidenzbasierter Zielstatus aus dem jeweils letzten zugeordneten Einzeltest

- datensparsame technische Ziel-Momentaufnahme pro Testlauf für eine verlässliche Historie nach Zieländerungen

- Zielstatus berücksichtigt Änderungen an Host, Port und AE-Titeln und verlangt danach einen neuen Test

- integrierte Hilfe und ehrlicher Kopfbereich ohne vorgetäuschte Anmeldung oder Benachrichtigungen

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

Unterstützt werden C-ECHO SCU, MWL C-FIND SCU, Study Root C-FIND SCU und C-STORE SCU. Für den schnellsten Systemcheck zuerst unter **Ziele** ein System anlegen. Details stehen in der [DICOM Support Matrix](docs/dicom-support.md). Bedienung: [User Manual](docs/user-manual.md). Fehleranalyse: [Troubleshooting](docs/troubleshooting.md).

> DCMSim hat im MVP keine Authentifizierung und ist ausschließlich für vertrauenswürdige interne Netze gedacht. Uploads können Patientendaten enthalten und werden nicht dauerhaft gespeichert. Es gibt keine Telemetrie oder Cloud-Kommunikation.
