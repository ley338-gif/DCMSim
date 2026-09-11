# ADR 0008: Separate Full-Stack-DICOM-Smoke-Tests

## Status

Akzeptiert

## Kontext

Gemockte Browser-Tests sind schnell, beweisen aber nicht das Zusammenspiel von UI, REST, Persistenz und DICOM-Netzwerk. Detaillierte DICOM-Integrationstests prüfen wiederum keinen Browser-Workflow.

## Entscheidung

Zwei separate Playwright-Smoke-Tests starten temporäres SQLite, FastAPI, React und lokale pynetdicom-SCPs. Geprüft werden ein realer MWL-C-FIND- und ein realer CT-C-STORE-Ablauf. Sie laufen in einem eigenen CI-Job und verwenden ausschließlich synthetische Daten.

## Konsequenzen

Die schnelle gemockte Suite bleibt erhalten. Der zusätzliche Job ist langsamer, lokal reproduzierbar und benötigt weder PACS noch RIS oder Internetdienst.
