# ADR-0002: pynetdicom for DICOM networking

**Status:** Accepted

**Context:** DICOM-Operationen müssen lokal, nachvollziehbar und ohne externe Kommandozeilenprogramme funktionieren.

**Decision:** pydicom modelliert Datasets; pynetdicom implementiert Association, C-ECHO, C-FIND und C-STORE direkt in Python.

**Consequences:** Ein einheitlicher Python-Stack und echte Netzwerk-Integrationstests; Protokollbesonderheiten bleiben explizite Anwendungslogik.

