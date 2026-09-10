# ADR-0006: Component-driven frontend architecture

**Status:** Accepted

**Context:** Worklist, PACS Store, Zielverwaltung und zukünftige DICOM-Werkzeuge benötigen dieselben Interaktions-, Status- und Diagnosemuster. Seitenspezifische Varianten würden Gestaltung und Verhalten auseinanderlaufen lassen.

**Decision:** Das Frontend verwendet zentrale Design Tokens und drei klar getrennte Komponentenebenen: `components/ui` für allgemeine Controls, `components/layout` für App-Shell und Seitenstruktur sowie `components/dicom` für fachliche Diagnosebausteine. Seiten orchestrieren diese Komponenten und beziehen Daten ausschließlich über den zentralen API-Service. Die nicht navigierte Route `/dev/ui` zeigt die verfügbaren Varianten.

**Consequences:** Neue DICOM-Module können bestehende Layout-, Formular-, Status-, Tabellen-, Log- und Metadatenkomponenten wiederverwenden. Änderungen am visuellen System sind zentral möglich. Die zusätzliche Komponentenebene erfordert bewusst gepflegte, stabile Props und Komponententests.
