# Architektur

## Systemüberblick

```text
Browser → React/TypeScript → REST → FastAPI
                                  ├── SQLAlchemy → SQLite /data/dcmsim.db
                                  └── pynetdicom → MWL/PACS im lokalen Netz
```

Frontend und Backend sind im Quellcode getrennt, werden im Container jedoch als ein Stack ausgeliefert. FastAPI liefert die gebauten statischen Dateien und die `/api`-Endpunkte aus. Es existieren weder externe Datenbank noch Queue oder Worker.

## Datenflüsse

Beim Worklist-Test validiert FastAPI den Endpunkt, baut ein pydicom-Query-Dataset und öffnet synchron eine begrenzte pynetdicom-Association. Pending-C-FIND-Antworten werden in Tabellenfelder und eine rekursive technische Darstellung übersetzt. Das Abschlussresultat wird in `test_runs` gespeichert.

Beim Store-Test erzeugt der Server ein gültiges monochromes Testobjekt mit neuen Study-, Series- und SOP-UIDs oder liest einen Upload aus dem Arbeitsspeicher. SOP Class und Transfer Syntax bilden genau einen angeforderten Presentation Context. Die C-STORE-Antwort und Objektidentifikatoren landen in der Historie.

Uploads werden größen- und endungsgeprüft, vollständig im Speicher gelesen, nach dem Request geschlossen und nie als Datei oder Pixelinhalt in der Datenbank gespeichert. Bei Fehlern werden interne Exceptions in stabile Codes übersetzt; Stacktraces erreichen den Browser nicht. Timeouts begrenzen TCP, Association und DIMSE.

Die SQLite-Persistenz enthält Ziele und Testläufe. SQLAlchemy hält die Geschäftslogik vom Datenbanktreiber getrennt; Alembic versioniert das Schema. Das lokale Deployment besteht aus einem Container und einem persistenten Volume.

