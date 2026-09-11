# Teststrategie

DCMSim testet kritische DICOM-Logik tiefer als statische Darstellung. Tests sind ohne PACS, RIS, Internet oder Patientendaten wiederholbar.

- **Unit:** AE-/Host-/Port-Validierung, Query-Builder, Dataset-Serialisierung, sechs synthetische Generatoren, Statusklassifikation, Modality-SOP-Mapping und kombinierte Ergebnislogik.
- **API-Integration:** REST-Validierung, Target- und Modalitätsprofil-CRUD, Fremdschlüsselverhalten sowie datensparsame History gegen temporäres SQLite.
- **Betriebsfunktionen:** Import-Upserts, ungültige Referenzen, Retention-Grenze und Lesbarkeit eines SQLite-Backups werden gegen temporäre Datenbanken geprüft.
- **DICOM-Integration:** echte pynetdicom-Associations für C-ECHO, C-STORE, MWL C-FIND und Study Root C-FIND gegen kurzlebige Localhost-SCPs auf freien Ports. MWL deckt `0xFF00`, `0xFF01`, finales `0x0000`, null Treffer, Reject, Abort, Failure und Timeout ab.
- **Frontend:** React Testing Library prüft fachliche Zustände, darunter Profilverwaltung, Zielauswahl, Calling-AE-Validierung, Dashboard-Integration aller Testtypen, Loading, vollständigen Erfolg und beide partiellen Fehlerpfade.
- **E2E mit kontrollierter API:** Playwright erhält die schnellen UI-Flows und prüft zusätzlich persistente Profilerstellung, die kombinierte Ergebnisdarstellung und die PACS-Studienansicht.
- **Full-Stack-Smoke:** Vier Playwright-Tests laufen ohne API-Mocks vom Browser über React, FastAPI und SQLite bis zu echten lokalen MWL-, Study-Root- und Storage-SCPs. Neben Worklist, Store und PACS-Suche deckt ein Test den vollständigen Modalitätsworkflow aus Zielanlage, Profil, kombiniertem Check und Historienaufruf ab. Sie ersetzen weder die schnellen E2E- noch die detaillierten Protokolltests.

Ausführung steht im [Development Guide](development.md). Coverage kann mit `pytest --cov=app --cov-report=html` erzeugt werden; Ziel ist hohe Abdeckung kritischer Domänenlogik statt einer künstlichen Prozentzahl.
