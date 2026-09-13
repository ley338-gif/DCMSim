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

Die Topologie verwendet zwei bewusst getrennte, feste Bäume: organisatorisch `Standort → Bereich → Modalitätsprofil`, technisch `DICOM-System → Endpoint`. Das Modalitätsformular konfiguriert den MWL-Endpoint, Station-AE-/Modalitätsfilter und STORE-Endpoint direkt. Die API bildet die MWL-Konfiguration transaktional auf einen internen Worklist-Kanal ab. Die UI gruppiert Profile nach Standort/Bereich und zeigt verwaiste Referenzen unter **Nicht zugeordnet**, statt sie zu verbergen oder einer anderen Struktur zuzuordnen.

Lokale Benutzerstandards werden validiert im Browser gespeichert. Das Frontend liest sie ausschließlich als Vorgaben für neue Formulare und Darstellungsoptionen; gespeicherte Ziele und Profile behalten ihre eigenen Werte. Serverseitige DICOM-Timeouts und Logging bleiben Container-Konfiguration und werden nicht durch Browserwerte überschrieben. Compose reicht die vier zugehörigen `DCMSIM_`-Variablen an den Container weiter. Ein schmaler, nur lesbarer API-Endpunkt zeigt die tatsächlich geladenen Werte, aber keine Datenbankadresse oder weiteren Konfigurationsgeheimnisse.

## Datenflüsse

Beim Worklist-Test validiert FastAPI den Endpunkt, baut ein pydicom-Query-Dataset und öffnet synchron eine begrenzte pynetdicom-Association. Pending-C-FIND-Antworten werden in Tabellenfelder und eine rekursive technische Darstellung übersetzt. Patientenbezogene Treffer liegen nur im Seitenzustand, nicht im Browser-Mutation-Cache. Ziel- oder Filteränderungen verwerfen die Anzeige und den Detaildialog; verspätete Antworten werden anhand einer Abfragekennung ignoriert. Ein bereits gestarteter DICOM-Lauf kann auf dem Server noch regulär enden. Das datensparsame technische Abschlussresultat wird in `test_runs` gespeichert.

Der aktuelle Browser erhält Trefferlisten und eingegebene Filter nur als unmittelbare Request-Antwort. Die zentrale Historiengrenze entfernt sie vor jeder Persistenz. Bei C-STORE bleiben technische UIDs und Aushandlungsdaten erhalten, während Patientenname und Patient-ID nicht gespeichert werden. Migration `0004` wendet dieselben Regeln irreversibel auf bereits vorhandene Historieneinträge an.

Die zentrale Logging-Konfiguration trennt Anwendungsereignisse von DICOM-Bibliotheksausgaben. `dcmsim.tests` protokolliert Endpunkt, AE Titles, Dauer, Ergebnis und Fehlerklasse; die Logger von pydicom und pynetdicom beginnen bei `WARNING`, damit deren ausführliche INFO-/DEBUG-Dataset-Dumps nicht in reguläre Container-Logs gelangen.

Die PACS-Suche verwendet das Study Root Query/Retrieve Information Model auf Level `STUDY`. Mindestens ein Filter verhindert unbeabsichtigte unbeschränkte Abfragen. Antwort-Datasets werden nur an den aktuellen Browser geliefert; die Historie speichert Status, Dauer und Trefferzahl, aber weder Patientenresultate noch patientenbezogene Suchfilter. Die Antwort liegt nur im Seitenzustand, nicht im Mutation-Cache; Ziel- oder Filteränderungen leeren sie. Eine Versionskennung je Suche verwirft verspätete Antworten für inzwischen geänderte Eingaben. Die DICOM-Operation auf dem Server kann dabei noch regulär enden und in der technischen Historie erscheinen. C-MOVE und C-GET sind getrennte, nicht implementierte Dienste.

Ein mögliches späteres C-MOVE wäre keine Erweiterung der HTTP-Portfreigabe: Ein Storage-SCP mit eigener AE und eingehendem DICOM-Port, PACS-seitigem Routing zur Move Destination, expliziter Netzwerk-/Firewall-Freigabe sowie Regeln für Patientendaten, Lebensdauer und Zugriff müssten separat entworfen und getestet werden. Die aktuelle Installation öffnet dafür keinen Listener.

Beim Store-Test erzeugt der Server ein gültiges monochromes Testobjekt mit neuen Study-, Series- und SOP-UIDs oder liest einen Upload aus dem Arbeitsspeicher. SOP Class und Transfer Syntax bilden genau einen angeforderten Presentation Context. C-ECHO und C-STORE haben im Browser getrennte Ergebniszustände. Ziel- und Testdatenänderungen verwerfen veraltete Transferanzeigen; eine Versionskennung verwirft verspätete Antworten. Dateianalysen verwenden eine eigene Versionskennung, damit entfernte oder ersetzte Uploads keine Metadaten nachliefern. Patientenbezogene Metadaten liegen nur im Seitenzustand, nicht im Mutation-Cache. Die datensparsame C-STORE-Antwort und Objektidentifikatoren landen in der Historie.

Ein Modalitätsprofil bildet ein Gerät ab und referenziert intern einen Worklist-Kanal sowie einen STORE-Endpoint. Der Inline-Orchestrierungsendpunkt verwendet einen vorhandenen Kanal nur bei vollständiger Übereinstimmung von Bereich, Modalität, MWL-Endpoint, beiden Modi und beiden festen Werten. Andernfalls erzeugt er einen deterministisch benannten internen Kanal und ändert keinen geteilten Kanal. Beim manuellen Modalitätscheck führt ein synchroner Service Worklist und Storage nacheinander aus. Die erste MWL-Abfrage wird niemals automatisch verbreitert. Nur ein zweiter Request mit `diagnostic_broad=true`, ausgelöst durch eine ausdrückliche Benutzeraktion, entfernt Station AE und Modalität; das aktuelle Datum bleibt gesetzt. Storage wählt für CT, MR, US, CR und DX die entsprechende SOP Class, andernfalls transparent Secondary Capture. Ein einzelner `modality_check`-Historieneintrag enthält die datensparsamen Subresultate, aber keine Worklist-Patientenlisten oder Suchfilter.

Uploads werden größen- und endungsgeprüft, vollständig im Speicher gelesen, nach dem Request geschlossen und nie als Datei oder Pixelinhalt in der Datenbank gespeichert. Bei Fehlern werden interne Exceptions in stabile Codes übersetzt; Stacktraces erreichen den Browser nicht. Timeouts begrenzen TCP, Association und DIMSE.

Die SQLite-Persistenz enthält weiterhin Legacy-Ziele und Testläufe sowie Standorte, Bereiche, DICOM-Systeme, Endpoints, Worklist-Kanäle und Modalitätsprofile. Migration `0007` ergänzt `worklist_channels.is_internal`; bestehende und v2-importierte Kanäle gelten sicherheitshalber als manuell verwaltet. Nur explizit interne, unreferenzierte Kanäle werden nach Profiländerung oder -löschung bereinigt. Organisatorisches Löschen setzt Profil- und Kanalzuordnungen auf `NULL`; Profile bleiben sichtbar. Ein verwendeter MWL-Endpoint ist durch `RESTRICT` geschützt. Migration `0006` kopiert jedes Legacy-Ziel in ein DICOM-System, erzeugt je aktiviertem Dienst einen Endpoint und bildet vorhandene Profile soweit möglich auf nicht zugeordnete Kanäle und STORE-Endpoints ab. Die alten Tabellen und Historienreferenzen bleiben erhalten. SQLAlchemy hält die Geschäftslogik vom Datenbanktreiber getrennt; Alembic versioniert das Schema. Neue Testläufe halten eine unveränderliche, datensparsame technische Ziel-Momentaufnahme fest. Die Historienansicht und der CSV-Export geben nur persistierte technische Felder aus.

Das Dashboard lädt nur sechs jüngste Testläufe für die Vorschau. Kennzahlen werden dagegen per SQL über die gesamte Historie aggregiert. Der Browser sendet die Grenzen seines lokalen Tages als Zeitzonen-bewusste Zeitpunkte; der Server normalisiert sie nach UTC und zählt innerhalb des halboffenen Intervalls. Das berücksichtigt auch Tage mit Sommerzeitwechsel und vermeidet eine fälschliche Begrenzung auf die letzten 100 Läufe.

Zeitstempel werden als UTC geschrieben. SQLite liefert `DateTime`-Werte ohne `tzinfo` zurück; die API-Read-Schemas und der CSV-Export kennzeichnen diese bekannten UTC-Werte vor der Ausgabe wieder ausdrücklich als UTC. Der Browser kann sie dadurch korrekt in seine lokale Zeitzone umrechnen. DICOM-Datumsfilter verwenden dagegen den lokalen Kalendertag des Browsers, weil Worklist- und Studienabfragen nach einem Kalenderdatum suchen.

Der Zielstatus vergleicht die technische Momentaufnahme des letzten zugeordneten Einzeltests mit der heutigen Konfiguration des passenden DICOM-Dienstes. C-ECHO kann einen beliebigen aktivierten Dienst geprüft haben; MWL, Store und Study Query sind dagegen dienstspezifisch. Fehlende Momentaufnahmen älterer Läufe gelten nicht als Nachweis für die aktuelle Konfiguration. Der Abgleich startet keinen Hintergrundtest und ist keine Überwachung.

Der Zielstatus ist keine Überwachung und erzeugt keine Hintergrundverbindungen. Ein read-only API-Endpunkt ermittelt pro Ziel den jüngsten direkt zugeordneten Testlauf. Das Frontend zeigt dessen Erfolg oder Fehler und Zeitpunkt; fehlt ein Lauf, bleibt der Status ausdrücklich ungeprüft. Kombinierte Modalitätsprüfungen werden keinem einzelnen Ziel zugerechnet, da ihre Subchecks verschiedene Ziele referenzieren können.

Betriebsfunktionen bleiben synchron und lokal: Der Export schreibt Topologieformat v2; der Import akzeptiert v2 und normalisiert weiterhin v1. Upserts verwenden feste fachliche Schlüssel (unter anderem Standortname, Bereich innerhalb Standort und Endpoint innerhalb System) und löschen keine nicht enthaltenen Daten. History-Retention wird ausschließlich manuell ausgelöst, und SQLite-Backups verwenden die Online-Backup-API der aktiven Verbindung. Ein Abbruch im Browser beendet das Warten des Clients; er verspricht keinen Abbruch einer bereits laufenden DIMSE-Operation.

## Produktgrenze zu HNR

Die strukturierte Auswahl macht DCMSim reproduzierbarer, erweitert es aber nicht zu einer allgemeinen Registry. DCMSim bleibt lokal, leichtgewichtig, diagnostisch und ohne Benutzerverwaltung. Die Hierarchie ist absichtlich fest und speichert nur für DICOM-Tests notwendige technische und organisatorische Bezeichner. Authentifizierung, Rollen, Audit, Dokumente, Dateien, beliebige Beziehungen, PostgreSQL-Mehrbenutzerbetrieb und organisationsweite Stammdaten gehören zum Healthcare Node Registry (HNR). Eine weitere Annäherung an diese Funktionen verlangt eine neue Produktentscheidung statt einer stillen Erweiterung des DCMSim-Modells.
