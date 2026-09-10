# ADR-0003: Synthetic test data by default

**Status:** Accepted

**Context:** PACS-Tests sollen keine echten Patientendaten benötigen.

**Decision:** DCMSim erzeugt standardmäßig eindeutig markierte Objekte mit `DCMSIM^TEST` und neuen UIDs.

**Consequences:** Sicherer, reproduzierbarer Standard. Eigene Uploads sind möglich, werden deutlich gewarnt und nie dauerhaft gespeichert.

