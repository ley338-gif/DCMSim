# ADR-0005: Synchronous DICOM operations in MVP

**Status:** Accepted

**Context:** Tests sind kurze, vom Nutzer gestartete Diagnosevorgänge und benötigen unmittelbare Ergebnisse.

**Decision:** DICOM-Operationen laufen synchron mit harten Connect-, Association- und DIMSE-Timeouts in FastAPIs Threadpool.

**Consequences:** Kein Worker oder Queue nötig und klarer Request-Lebenszyklus. Sehr hohe Parallelität ist kein Ziel; längere Aufgaben erfordern später ein anderes Ausführungsmodell.

