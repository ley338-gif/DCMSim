# Architektur

## Systemüberblick

```text
Browser → React/TypeScript → REST → FastAPI
                                  ├── SQLAlchemy → SQLite /data/dcmsim.db
                                  └── pynetdicom → MWL/PACS im lokalen Netz
```

Frontend und Backend sind im Quellcode getrennt, werden im Container jedoch als ein Stack ausgeliefert. FastAPI liefert die gebauten statischen Dateien und die `/api`-Endpunkte aus. Es existieren weder externe Datenbank noch Queue oder Worker.

## Frontend-Architektur und Designsystem

Das React-Frontend besteht aus drei wiederverwendbaren Ebenen:

- `components/ui`: Buttons, Karten, Form Controls, Tabellen, Status, Alerts, Overlays und Progress.
- `components/layout`: AppShell, responsive Sidebar, Topbar und PageHeader.
- `components/dicom`: TargetSelector, Result Summary, Transfer Progress, DICOM Log und Metadata Panel.

Farb-, Abstands-, Typografie-, Radius-, Shadow-, Control- und Z-Index-Tokens liegen zentral unter `src/theme/tokens.css`. Feature-Seiten orchestrieren die Bausteine und greifen über `src/api/client.ts` auf die REST-API zu. Loading-, Empty-, Success-, Warning- und Error-Zustände sind Teil der Komponenten. Unter `/dev/ui` existiert eine interne, nicht navigierte Showcase-Seite.

## Datenflüsse

Beim Worklist-Test validiert FastAPI den Endpunkt, baut ein pydicom-Query-Dataset und öffnet synchron eine begrenzte pynetdicom-Association. Pending-C-FIND-Antworten werden in Tabellenfelder und eine rekursive technische Darstellung übersetzt. Das Abschlussresultat wird in `test_runs` gespeichert.

Beim Store-Test erzeugt der Server ein gültiges monochromes Testobjekt mit neuen Study-, Series- und SOP-UIDs oder liest einen Upload aus dem Arbeitsspeicher. SOP Class und Transfer Syntax bilden genau einen angeforderten Presentation Context. Die C-STORE-Antwort und Objektidentifikatoren landen in der Historie.

Ein Modalitätsprofil bildet ein Gerät ab und referenziert bestehende Ziele getrennt für MWL und Storage. Beim manuellen Modalitätscheck führt ein synchroner Service die aktivierten Prüfungen nacheinander aus. MWL verwendet zunächst Datum, Modalität und Calling AE als Station AE; bei null Treffern folgt eine rein diagnostische Abfrage ohne Station AE. Storage wählt für CT, MR, US, CR und DX die entsprechende SOP Class, andernfalls transparent Secondary Capture. Ein einzelner `modality_check`-Historieneintrag enthält die Subresultate, aber keine Worklist-Patientenlisten.

Uploads werden größen- und endungsgeprüft, vollständig im Speicher gelesen, nach dem Request geschlossen und nie als Datei oder Pixelinhalt in der Datenbank gespeichert. Bei Fehlern werden interne Exceptions in stabile Codes übersetzt; Stacktraces erreichen den Browser nicht. Timeouts begrenzen TCP, Association und DIMSE.

Die SQLite-Persistenz enthält Ziele, Modalitätsprofile und Testläufe. Beim Löschen eines Ziels setzt die Datenbank Profilreferenzen auf `NULL`; ein betroffenes Profil bleibt sichtbar, kann aber erst nach Wahl eines neuen Ziels wieder geprüft werden. SQLAlchemy hält die Geschäftslogik vom Datenbanktreiber getrennt; Alembic versioniert das Schema. Das lokale Deployment besteht aus einem Container und einem persistenten Volume.
