# Teststrategie

DCMSim testet kritische DICOM-Logik tiefer als statische Darstellung. Tests sind ohne PACS, RIS, Internet oder Patientendaten wiederholbar.

- **Unit:** AE-/Host-/Port-Validierung, Query-Builder, Dataset-Serialisierung, sechs synthetische Generatoren, Statusklassifikation, Modality-SOP-Mapping und kombinierte Ergebnislogik.
- **API-Integration:** REST-Validierung, Target- und Modalitätsprofil-CRUD, Fremdschlüsselverhalten und History gegen temporäres SQLite.
- **DICOM-Integration:** echte pynetdicom-Associations für C-ECHO, C-STORE und MWL C-FIND gegen kurzlebige Localhost-SCPs auf freien Ports. MWL deckt `0xFF00`, `0xFF01`, finales `0x0000`, null Treffer, Reject, Abort, Failure und Timeout ab.
- **Frontend:** React Testing Library prüft fachliche Zustände, darunter Profilverwaltung, Zielauswahl, Calling-AE-Validierung, Loading, vollständigen Erfolg und beide partiellen Fehlerpfade.
- **E2E mit kontrollierter API:** Playwright erhält die schnellen UI-Flows und prüft zusätzlich persistente Profilerstellung sowie die kombinierte Ergebnisdarstellung.
- **Full-Stack-Smoke:** Drei Playwright-Tests laufen ohne API-Mocks vom Browser über React, FastAPI und SQLite bis zu echten lokalen MWL- und Storage-SCPs. Neben den einzelnen Worklist- und Store-Strecken deckt ein Test den vollständigen 0.2-Workflow aus Zielanlage, Modalitätsprofil, kombiniertem Check und Historienaufruf ab. Sie ersetzen weder die schnellen E2E- noch die detaillierten Protokolltests.

Ausführung steht im [Development Guide](development.md). Coverage kann mit `pytest --cov=app --cov-report=html` erzeugt werden; Ziel ist hohe Abdeckung kritischer Domänenlogik statt einer künstlichen Prozentzahl.
