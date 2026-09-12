# Architektur

## Systemüberblick

```text
Browser → React/TypeScript → REST → FastAPI
                                  ├── SQLAlchemy → SQLite /data/dcmsim.db
                                  └── pynetdicom → MWL/PACS im lokalen Netz
```

Frontend und Backend sind im Quellcode getrennt, werden im Container jedoch als ein Stack ausgeliefert. FastAPI liefert die gebauten statischen Dateien und die `/api`-Endpunkte aus. Es existieren weder externe Datenbank noch Queue oder Worker.

Docker Compose veröffentlicht den Container-Port standardmäßig nur auf der IPv4-Loopback-Adresse des Hosts (`127.0.0.1:8080`). `DCMSIM_PUBLISH_HOST` kann für einen bewusst abgesicherten Netzwerkzugriff auf eine private Host-Adresse gesetzt werden. Der Prozess im Container lauscht weiterhin auf `0.0.0.0`, damit die Portweiterleitung funktioniert; daraus folgt keine Veröffentlichung auf allen Host-Schnittstellen. DCMSim selbst bietet keine Authentifizierung.

Diese Host-Portbindung betrifft nur eingehendes HTTP. Ausgehende DICOM-Verbindungen nutzen die Docker-Netzwerkroute und werden im CI mit einem getrennten Verification-SCP geprüft. Ein DICOM-Ziel `127.0.0.1` meint aus Sicht des Containers den Container selbst; für Dienste auf dem Host oder im Netz muss eine von dort erreichbare Adresse konfiguriert werden.

`/api/health` ist eine reine Liveness-Prüfung des Webdienstes. `/api/ready` führt zusätzlich eine Datenbankabfrage aus und liefert bei Datenbankfehlern HTTP 503 ohne interne Fehlerdetails. Docker verwendet Readiness als Healthcheck. Weder Liveness noch Readiness baut eine DICOM-Verbindung zu gespeicherten Zielen auf.

## Frontend-Architektur und Designsystem

Das React-Frontend besteht aus drei wiederverwendbaren Ebenen:

- `components/ui`: Buttons, Karten, Form Controls, Tabellen, Status, Alerts, Overlays und Progress.
- `components/layout`: AppShell, responsive Sidebar, Topbar und PageHeader.
- `components/dicom`: TargetSelector, Result Summary, Transfer Progress, DICOM Log und Metadata Panel.

Farb-, Abstands-, Typografie-, Radius-, Shadow-, Control- und Z-Index-Tokens liegen zentral unter `src/theme/tokens.css`. Feature-Seiten orchestrieren die Bausteine und greifen über `src/api/client.ts` auf die REST-API zu. Loading-, Empty-, Success-, Warning- und Error-Zustände sind Teil der Komponenten. Unter `/dev/ui` existiert eine interne, nicht navigierte Showcase-Seite.

Lokale Benutzerstandards werden validiert im Browser gespeichert. Das Frontend liest sie ausschließlich als Vorgaben für neue Formulare und Darstellungsoptionen; gespeicherte Ziele und Profile behalten ihre eigenen Werte. Serverseitige DICOM-Timeouts und Logging bleiben Container-Konfiguration und werden nicht durch Browserwerte überschrieben.

## Datenflüsse

Beim Worklist-Test validiert FastAPI den Endpunkt, baut ein pydicom-Query-Dataset und öffnet synchron eine begrenzte pynetdicom-Association. Pending-C-FIND-Antworten werden in Tabellenfelder und eine rekursive technische Darstellung übersetzt. Das Abschlussresultat wird in `test_runs` gespeichert.

Der aktuelle Browser erhält Trefferlisten und eingegebene Filter nur als unmittelbare Request-Antwort. Die zentrale Historiengrenze entfernt sie vor jeder Persistenz. Bei C-STORE bleiben technische UIDs und Aushandlungsdaten erhalten, während Patientenname und Patient-ID nicht gespeichert werden. Migration `0004` wendet dieselben Regeln irreversibel auf bereits vorhandene Historieneinträge an.

Die zentrale Logging-Konfiguration trennt Anwendungsereignisse von DICOM-Bibliotheksausgaben. `dcmsim.tests` protokolliert Endpunkt, AE Titles, Dauer, Ergebnis und Fehlerklasse; die Logger von pydicom und pynetdicom beginnen bei `WARNING`, damit deren ausführliche INFO-/DEBUG-Dataset-Dumps nicht in reguläre Container-Logs gelangen.

Die PACS-Suche verwendet das Study Root Query/Retrieve Information Model auf Level `STUDY`. Mindestens ein Filter verhindert unbeabsichtigte unbeschränkte Abfragen. Antwort-Datasets werden nur an den aktuellen Browser geliefert; die Historie speichert Status, Dauer und Trefferzahl, aber weder Patientenresultate noch patientenbezogene Suchfilter. C-MOVE und C-GET sind getrennte, nicht implementierte Dienste.

Ein mögliches späteres C-MOVE wäre keine Erweiterung der HTTP-Portfreigabe: Ein Storage-SCP mit eigener AE und eingehendem DICOM-Port, PACS-seitigem Routing zur Move Destination, expliziter Netzwerk-/Firewall-Freigabe sowie Regeln für Patientendaten, Lebensdauer und Zugriff müssten separat entworfen und getestet werden. Die aktuelle Installation öffnet dafür keinen Listener.

Beim Store-Test erzeugt der Server ein gültiges monochromes Testobjekt mit neuen Study-, Series- und SOP-UIDs oder liest einen Upload aus dem Arbeitsspeicher. SOP Class und Transfer Syntax bilden genau einen angeforderten Presentation Context. Die C-STORE-Antwort und Objektidentifikatoren landen in der Historie.

Ein Modalitätsprofil bildet ein Gerät ab und referenziert bestehende Ziele getrennt für MWL und Storage. Beim manuellen Modalitätscheck führt ein synchroner Service die aktivierten Prüfungen nacheinander aus. MWL verwendet zunächst Datum, Modalität und Calling AE als Station AE; bei null Treffern folgt eine rein diagnostische Abfrage ohne Station AE. Storage wählt für CT, MR, US, CR und DX die entsprechende SOP Class, andernfalls transparent Secondary Capture. Ein einzelner `modality_check`-Historieneintrag enthält die Subresultate, aber keine Worklist-Patientenlisten.

Uploads werden größen- und endungsgeprüft, vollständig im Speicher gelesen, nach dem Request geschlossen und nie als Datei oder Pixelinhalt in der Datenbank gespeichert. Bei Fehlern werden interne Exceptions in stabile Codes übersetzt; Stacktraces erreichen den Browser nicht. Timeouts begrenzen TCP, Association und DIMSE.

Die SQLite-Persistenz enthält Ziele, Modalitätsprofile und Testläufe. Beim Löschen eines Ziels setzt die Datenbank Profilreferenzen auf `NULL`; ein betroffenes Profil bleibt sichtbar, kann aber erst nach Wahl eines neuen Ziels wieder geprüft werden. SQLAlchemy hält die Geschäftslogik vom Datenbanktreiber getrennt; Alembic versioniert das Schema. Neue Testläufe halten eine unveränderliche, datensparsame technische Ziel-Momentaufnahme (Name, Host, Port, AE-Titel) fest; sie enthält keine Suchfilter oder Patientendaten. Die Historienansicht nutzt eine serverseitige, paginierte Abfrage; ein separater CSV-Endpunkt verwendet dieselben Filter und gibt nur die datensparsam persistierten technischen Felder aus. Das lokale Deployment besteht aus einem Container und einem persistenten Volume.

Das Dashboard lädt nur sechs jüngste Testläufe für die Vorschau. Kennzahlen werden dagegen per SQL über die gesamte Historie aggregiert. Der Browser sendet die Grenzen seines lokalen Tages als Zeitzonen-bewusste Zeitpunkte; der Server normalisiert sie nach UTC und zählt innerhalb des halboffenen Intervalls. Das berücksichtigt auch Tage mit Sommerzeitwechsel und vermeidet eine fälschliche Begrenzung auf die letzten 100 Läufe.

Der Zielstatus vergleicht die technische Momentaufnahme des letzten zugeordneten Einzeltests mit der heutigen Konfiguration des passenden DICOM-Dienstes. C-ECHO kann einen beliebigen aktivierten Dienst geprüft haben; MWL, Store und Study Query sind dagegen dienstspezifisch. Fehlende Momentaufnahmen älterer Läufe gelten nicht als Nachweis für die aktuelle Konfiguration. Der Abgleich startet keinen Hintergrundtest und ist keine Überwachung.

Der Zielstatus ist keine Überwachung und erzeugt keine Hintergrundverbindungen. Ein read-only API-Endpunkt ermittelt pro Ziel den jüngsten direkt zugeordneten Testlauf. Das Frontend zeigt dessen Erfolg oder Fehler und Zeitpunkt; fehlt ein Lauf, bleibt der Status ausdrücklich ungeprüft. Kombinierte Modalitätsprüfungen werden keinem einzelnen Ziel zugerechnet, da ihre Subchecks verschiedene Ziele referenzieren können.

Betriebsfunktionen bleiben synchron und lokal: Konfigurationsimporte sind namensbasierte Upserts ohne Löschung, History-Retention wird ausschließlich manuell ausgelöst, und SQLite-Backups verwenden die Online-Backup-API der aktiven Verbindung. Ein Abbruch im Browser beendet das Warten des Clients; er verspricht keinen Abbruch einer bereits laufenden DIMSE-Operation.
