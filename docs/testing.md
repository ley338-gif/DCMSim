# Teststrategie

DCMSim testet kritische DICOM-Logik tiefer als statische Darstellung. Tests sind ohne PACS, RIS, Internet oder Patientendaten wiederholbar.

- **Unit:** AE-/Host-/Port-Validierung, Query-Builder, Dataset-Serialisierung, sechs synthetische Generatoren, Statusklassifikation, Modality-SOP-Mapping und kombinierte Ergebnislogik.
- **API-Integration:** REST-Validierung, CRUD für Standorte, Bereiche, DICOM-Systeme, Endpoints, Worklist-Kanäle und Modalitätsprofile, Fremdschlüsselverhalten sowie datensparsame History gegen temporäres SQLite.
- **Betriebsfunktionen:** Import-Upserts, ungültige Referenzen, Retention-Grenze und Lesbarkeit eines SQLite-Backups werden gegen temporäre Datenbanken geprüft.
- **DICOM-Integration:** echte pynetdicom-Associations für C-ECHO, C-STORE, MWL C-FIND und Study Root C-FIND gegen kurzlebige Localhost-SCPs auf freien Ports. MWL deckt `0xFF00`, `0xFF01`, finales `0x0000`, null Treffer, Reject, Abort, Failure und Timeout ab.
- **Migration:** `0006` wird auf eine echte Datenbank des Schemas `0005` angewendet und beweist die Normalisierung von Legacy-Zielen, Profilreferenzen und die unveränderte Historie.
- **Frontend:** React Testing Library prüft CRUD-Aufrufe, gruppierte Profile, **Nicht zugeordnet**, strukturierte Kanal-/Endpoint-Auswahl, API-Fehlerzustände, Importvorschau, Calling-AE-Validierung und die nur explizit ausgelöste breite Diagnose.
- **E2E mit kontrollierter API:** Playwright prüft Navigation zu **Systeme**, sichtbare Standorte/Endpoints/Kanäle, strukturierte persistente Profilerstellung, Importvorschau, kombinierte Ergebnisse und PACS-Studienansicht.
- **Full-Stack-Smoke:** Vier Playwright-Tests laufen ohne API-Mocks vom Browser über React, FastAPI und SQLite bis zu echten lokalen MWL-, Study-Root- und Storage-SCPs. Neben Worklist, Store und PACS-Suche legt ein Test Standort, Bereich, System, echte MWL-/STORE-Endpoints, Kanal und Profil an und prüft anschließend kombiniert gegen die realen SCPs sowie die Historie. API-Mocks ersetzen diese Protokoll-Smokes nicht.

Ausführung steht im [Development Guide](development.md). Die Frontend-CI prüft nach `npm ci` mit `npm audit --audit-level=moderate` die vollständige Abhängigkeitsliste einschließlich der Testwerkzeuge. Coverage kann mit `pytest --cov=app --cov-report=html` erzeugt werden; Ziel ist hohe Abdeckung kritischer Domänenlogik statt einer künstlichen Prozentzahl.
