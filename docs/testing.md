# Teststrategie

DCMSim testet kritische DICOM-Logik tiefer als statische Darstellung. Tests sind ohne PACS, RIS, Internet oder Patientendaten wiederholbar.

- **Unit:** AE-/Host-/Port-Validierung, MWL-Query- und Broad-Query-Builder, Sequenzparser, Dataset-Serialisierung, synthetische UIDs/Pixel, SOP-/Transfer-Mapping und Statusklassifikation.
- **API-Integration:** REST-Validierung und Target-CRUD gegen temporäres echtes SQLite-Schema. Uploads bleiben im Speicher und werden geschlossen.
- **DICOM-Integration:** echte pynetdicom-Associations für C-ECHO und C-STORE gegen kurzlebige Localhost-SCPs auf freien Ports. Fehlerwrapper und seltene Timeout-Pfade dürfen isoliert gemockt werden.
- **Frontend:** React Testing Library prüft Button-Zustände, Status-Badges, Target-Auswahl, Tastaturbedienung der DataTable, Transferfortschritt, technische Logs und stabile Fehlerdarstellung. Seitenflows decken Formzustände, Nulltreffer und UIDs ab.
- **E2E:** Playwright prüft Kernnavigation, Worklist-Nulltreffer-Diagnose und PACS-Erfolg; API-Antworten werden für stabile UI-Flows kontrolliert. Die tatsächliche DICOM-Netzwerkstrecke wird separat in den DICOM-Integrationstests nicht gemockt.

Ausführung steht im [Development Guide](development.md). Coverage kann mit `pytest --cov=app --cov-report=html` erzeugt werden; Ziel ist hohe Abdeckung kritischer Domänenlogik statt einer künstlichen Prozentzahl.
