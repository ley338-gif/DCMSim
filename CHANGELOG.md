# Changelog

Alle relevanten Änderungen werden nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) dokumentiert. Das Projekt verwendet Semantic Versioning.

## [Unreleased]

### Added

- Noch keine Änderungen.

## [0.3.22] - 2026-09-13

### Changed

- Zielstatus auf Übersicht und Zielseite nennt jetzt den Typ des letzten Einzeltests (C-ECHO, Worklist C-FIND, PACS C-FIND oder C-STORE) und verlinkt dessen Historieneintrag.
- So ist ein erfolgreicher C-ECHO-Test nicht mehr mit einer erfolgreichen Storage- oder Worklist-Prüfung zu verwechseln.
- Produktversion auf 0.3.22 angehoben.

## [0.3.21] - 2026-09-12

### Fixed

- Die Auswahl einer Konfigurationsdatei startet keinen überschreibenden Import mehr. Eine Vorschau nennt neue und gleichnamige bestehende Ziele und Profile; erst die Bestätigung führt den Import aus.
- Importdateien mit doppelten Ziel- oder Profilnamen werden mit einem Validierungsfehler abgewiesen, ohne bestehende Konfiguration zu verändern.

### Changed

- Produktversion auf 0.3.21 angehoben.

## [0.3.20] - 2026-09-12

### Added

- Die Testhistorie kann nach lokalen Kalendertagen („Von“ und „Bis“) gefiltert werden; der CSV-Export verwendet denselben Zeitraum.
- Die API akzeptiert eindeutige Zeitgrenzen mit Zeitzonenoffset und weist ungültige oder vertauschte Grenzen zurück.

### Changed

- Produktversion auf 0.3.20 angehoben.

## [0.3.19] - 2026-09-12

### Security

- Vitest und `@vitest/mocker` auf die korrigierte Version 4.1.11 aktualisiert; damit sind die zwei Meldungen zum Redirect-Mock-Path-Traversal behoben.
- Die Frontend-CI führt `npm audit --audit-level=moderate` aus, damit entsprechende neue Abhängigkeitsmeldungen sichtbar und prüfpflichtig werden.

### Changed

- Produktversion auf 0.3.19 angehoben.

## [0.3.18] - 2026-09-12

### Fixed

- C-ECHO wird im PACS Store getrennt vom C-STORE-Transfer angezeigt und kann keinen vermeintlichen erfolgreichen C-STORE mehr auslösen.
- Änderungen an Ziel, SOP Class, Transfer Syntax, Testmodus oder Datei entfernen alte Transferresultate; verspätete Antworten werden nicht zur neuen Eingabe angezeigt.
- Verspätete Analyseantworten bereits entfernter oder ersetzter DICOM-Dateien erscheinen nicht mehr. Ohne ausgewählte Datei werden keine synthetischen Patientendaten im Upload-Modus vorgetäuscht.

### Changed

- C-STORE-Antworten bleiben ausschließlich im aktuellen Seitenzustand statt zusätzlich im Browser-Mutation-Cache.
- Produktversion auf 0.3.18 angehoben.

## [0.3.17] - 2026-09-12

### Fixed

- Worklist-Treffer und geöffnete DICOM-Details verschwinden bei Ziel- oder Filteränderungen. Verspätete Antworten früherer Abfragen erscheinen nicht mehr zu neuen Eingaben.
- Diagnose-Wiederholungen ohne Station AE beziehungsweise Modalität verwenden den aktualisierten Filtersatz und können nicht unkontrolliert parallel zur laufenden Abfrage gestartet werden.

### Changed

- Patientenbezogene Worklist-Antworten liegen nur im aktuellen Seitenzustand statt zusätzlich im Browser-Mutation-Cache.
- Produktversion auf 0.3.17 angehoben.

## [0.3.16] - 2026-09-12

### Fixed

- PACS-Studienergebnisse und der Detaildialog werden beim Ändern von Ziel oder Filtern sofort ausgeblendet. Verspätete Antworten einer älteren Abfrage erscheinen nicht unter neuen Suchkriterien.

### Changed

- Die PACS-Suche hält patientenbezogene Antwortdaten nur im aktuellen Seitenzustand und nicht zusätzlich im Mutation-Cache des Browsers.
- Produktversion auf 0.3.16 angehoben.

## [0.3.15] - 2026-09-12

### Fixed

- Die Einstellungen bieten für Server-Timeouts und Log Level keine wirkungslosen, scheinbar speicherbaren Browser-Eingaben mehr an.

### Added

- Die tatsächlich wirksamen Server-Timeouts und das Log Level sind in den Einstellungen nur lesbar sichtbar. Der neue API-Endpunkt gibt keine Datenbankadresse oder andere vertrauliche Konfiguration aus.
- Docker Compose reicht konfigurierte Timeout- und Log-Level-Werte aus der lokalen Umgebung an den Container weiter.

### Changed

- Produktversion auf 0.3.15 angehoben.

## [0.3.14] - 2026-09-12

### Fixed

- API und Historien-CSV kennzeichnen gespeicherte UTC-Zeitstempel ausdrücklich mit Zeitzone, auch wenn SQLite diese Information beim Lesen entfernt. Browser zeigen damit lokale Uhrzeiten korrekt an.
- Worklist und PACS-Suche verwenden beim Öffnen der Seite den lokalen Kalendertag statt des UTC-Datums als vorbelegten Filter.

### Changed

- Produktversion auf 0.3.14 angehoben.

## [0.3.13] - 2026-09-12

### Fixed

- Dashboard-Kennzahlen für heutige Tests, Erfolgsquote und Testverteilung einschließlich C-ECHO werden über die gesamte Historie serverseitig aggregiert und bleiben bei mehr als 100 Einträgen korrekt.
- Der heutige Zeitraum folgt den lokalen Tagesgrenzen des Browsers; die API verlangt eindeutige Zeitzonenangaben und begrenzt den Zeitraum.

### Changed

- Die Übersicht lädt für die Tabelle nur noch die sechs letzten Testläufe.
- Produktversion auf 0.3.13 angehoben.

## [0.3.12] - 2026-09-12

### Added

- Docker-CI prüft per echtem C-ECHO vom Anwendungscontainer zu einem separaten Test-SCP, dass ausgehende DICOM-Verbindungen trotz lokaler Web-Portbindung funktionieren.
- Hilfe und Betriebsdokumentation erklären, dass `127.0.0.1` als DICOM-Ziel im Container nur den Container selbst bezeichnet.

### Changed

- Produktversion auf 0.3.12 angehoben.

## [0.3.11] - 2026-09-12

### Added

- Separate Datenbank-Bereitschaftsprüfung unter `/api/ready`; Docker kennzeichnet den Container anhand dieser Prüfung als gesund oder ungesund.
- Betriebsdokumentation erklärt den Unterschied zwischen Web-Liveness, Datenbank-Readiness und DICOM-Zieltests.
- Die Voraussetzungen für ein mögliches späteres C-MOVE werden ohne vorzeitige Portfreigabe dokumentiert.

### Changed

- Produktversion auf 0.3.11 angehoben.

## [0.3.10] - 2026-09-12

### Changed

- Docker Compose veröffentlicht Port 8080 standardmäßig nur auf `127.0.0.1` statt auf allen Host-Schnittstellen.
- Netzwerkzugriff erfordert eine explizite private Host-Adresse über `DCMSIM_PUBLISH_HOST` und eigene Zugangssicherung.
- Integrierte Hilfe, Betriebsdokumentation und CI-Prüfungen erklären und überprüfen diesen Sicherheitsstandard.
- Produktversion auf 0.3.10 angehoben.

## [0.3.9] - 2026-09-12

### Added

- Integrierte Hilfeseite mit Schnellstart, Statusdeutung, Fehlersuche, Datenschutz und DICOM-Grenzen.
- Direkte Wege von der Kopfzeile zu Hilfe und Testhistorie; das Logo führt zur Übersicht.
- Browser-Regressionstests für die neue Navigation und den sichtbaren Hinweis auf den Betrieb ohne Anmeldung.

### Changed

- Entfernt funktionslose Benachrichtigungs- und vermeintliche Admin-Bedienelemente. Die Kopfzeile zeigt stattdessen den tatsächlichen unauthentifizierten Betrieb an.
- Produktversion auf 0.3.9 angehoben.

## [0.3.8] - 2026-09-12

### Added

- Konfigurationsabgleich für den letzten Einzeltest jedes Ziels: Host, Dienst-Port, Called AE, Calling AE und aktivierter Dienst.
- Regressionstests für geänderte, unveränderte und ältere nicht belegbare Zielkonfigurationen.

### Changed

- Dashboard und Zielverwaltung zeigen einen alten Erfolg nach technischen Zieländerungen als „Erneut prüfen“ statt als aktuellen Erfolg.
- Tests ohne technische Momentaufnahme werden als „Nicht belegbar“ gekennzeichnet; reine Namensänderungen lassen einen gültigen technischen Test bestehen.
- Nach dem Speichern eines Ziels wird der Zielstatus sofort neu geladen.
- Produktversion auf 0.3.8 angehoben.

## [0.3.7] - 2026-09-12

### Added

- Neue Datenbankmigration für technische Ziel-Momentaufnahmen je Testlauf (Name, Host, Port, Calling/Called AE; keine Patientenwerte).
- Regressionstests für unveränderliche Historienwerte nach Umbenennung und Hostwechsel eines Ziels.

### Changed

- Historienliste, Testdetails, Suche und CSV verwenden für neue Läufe die tatsächlich verwendete Zielkonfiguration statt der später möglicherweise geänderten Stammdaten.
- Ältere Läufe ohne Momentaufnahme bleiben lesbar und zeigen unbekannte technische Felder ausdrücklich als nicht gespeichert an.
- Produktversion auf 0.3.7 angehoben.

## [0.3.6] - 2026-09-12

### Added

- API-Zusammenfassung des jeweils letzten direkt einem Ziel zugeordneten Testlaufs.
- Wiederverwendbare Zielstatusanzeige mit Ergebnis und Prüfzeitpunkt.
- Backend-, Frontend- und Browsertests für erfolgreiche, fehlgeschlagene und ungeprüfte Ziele.

### Changed

- Dashboard und Zielverwaltung zeigen nicht mehr pauschal „Konfiguriert“, sondern ausschließlich gemessene Testergebnisse oder „Ungeprüft“.
- Manuelle Verbindungstests beim Bearbeiten eines gespeicherten Ziels werden diesem Ziel zugeordnet und aktualisieren den Status direkt.
- Zielnamen aus dem gespeicherten Testergebnis ersetzen nach Möglichkeit technische Ziel-IDs in der Dashboard-Historie.
- Produktversion auf 0.3.6 angehoben.

## [0.3.5] - 2026-09-12

### Added

- Zentral validierte lokale Einstellungen mit sicheren Standardwerten bei beschädigtem Browser-Speicher.
- Regressionstests für die Übernahme des Calling AE in neue Tests, Ziele und Modalitätsprofile.

### Changed

- Das gespeicherte Default Calling AE wird für neue manuelle Worklist-, Store- und PACS-Suchabfragen sowie neue Ziele und Modalitätsprofile verwendet.
- Die kompakte Tabellenansicht wird nach dem Speichern sofort und beim nächsten Start automatisch angewendet.
- Die Einstellungsseite kennzeichnet serverseitige Timeout- und Logging-Werte weiterhin ausdrücklich als Container-Konfiguration.
- Produktversion auf 0.3.5 angehoben.

## [0.3.4] - 2026-09-12

### Added

- Paginierte serverseitige Historienabfrage mit Filtern für Testtyp, Erfolg und technische Freitextfelder.
- CSV-Export der aktuell gefilterten Historie mit UTF-8-Kodierung und Schutz vor Tabellenformeln.
- Backend- und Frontend-Regressionstests für Filterung, Pagination und datensparsamen Export.

### Changed

- Die Historienseite lädt jeweils höchstens 50 Testläufe und zeigt die Gesamtzahl sowie Vor-/Zurück-Navigation an.
- Der CSV-Export enthält ausschließlich technische Historienfelder und keine Worklist- oder PACS-Trefferlisten.
- Produktversion auf 0.3.4 angehoben.

## [0.3.3] - 2026-09-12

### Added

- Zentrale Logging-Konfiguration und Regressionstests für die DICOM-Bibliothekslogger.

### Changed

- pydicom und pynetdicom protokollieren unabhängig vom Application Log Level erst ab `WARNING`, damit reguläre Container-Logs keine vollständigen DICOM-Datasets enthalten.
- Ungültige Werte für das Application Log Level fallen sicher auf `INFO` zurück.
- Produktversion auf 0.3.3 angehoben.

## [0.3.2] - 2026-09-12

### Added

- Datenmigration `0004`, die Patientenresultate und patientenbezogene Filter aus vorhandenen Historieneinträgen entfernt.
- Datenschutztests für Worklist-, PACS-Such- und C-STORE-Historie.

### Changed

- Die zentrale Historienpersistenz entfernt bei Worklist und PACS-Suche Trefferlisten sowie Suchfilter und bei C-STORE Patientenname und Patient-ID.
- Technische Kennzahlen, Status, Laufzeit und DICOM-UIDs bleiben zur Fehleranalyse erhalten.
- Produktversion auf 0.3.2 angehoben.

## [0.3.1] - 2026-09-12

### Added

- Regressionstest für die vollständige Dashboard-Darstellung von PACS-Suche und Modalitätsprüfungen.

### Changed

- Übersicht um PACS-Suche als Schnelltest und Query/Retrieve SCU im Systemstatus ergänzt.
- Zielstatus, Testverteilung, letzte Tests und konfigurierte Dienste berücksichtigen nun Query/Retrieve und Modalitätsprüfungen vollständig.
- Produktversion auf 0.3.1 angehoben.

## [0.3.0] - 2026-09-11

### Added

- PACS-Studienabfrage per Study Root Query/Retrieve Information Model C-FIND.
- Separate Query/Retrieve-Endpunkte an gespeicherten Zielen.
- Tabellen- und DICOM-Detailansicht für Studienantworten sowie Historientyp `qr_find`.
- Reale Localhost-DICOM-Integration und Browsertests für die PACS-Suche.

### Changed

- Produktversion auf 0.3.0 angehoben.
- Studienabfragen verlangen mindestens ein Suchkriterium; Patientenresultate und patientenbezogene Filter werden nicht in der Historie persistiert.

## [0.2.1] - 2026-09-11

### Added

- Echter Full-Stack-Smoke-Test für den vollständigen Modalitätsworkflow von Ziel- und Profilerstellung bis zur gespeicherten kombinierten Prüfung.
- Nicht löschender JSON-Export und -Import für Ziele und Modalitätsprofile.
- Konsistentes SQLite-Backup über die laufende Datenbankverbindung.
- Manuell konfigurierbare Bereinigung alter Historieneinträge ohne Scheduler.
- Konkrete Handlungsempfehlungen für klassifizierte DICOM-Fehler.
- Abbrechen der Browseranzeige und direktes Wiederholen eines Modalitätschecks.

### Changed

- Unvollständige Profile nach einer Ziel-Löschung werden klar markiert und können vor der Reparatur nicht geprüft werden.
- Zielnamen erscheinen konsistent in technischen Testresultaten.
- Mobile Modalitätskarten, Dialoge, Statusmeldungen und Tastaturnavigation wurden verbessert.

## [0.2.0] - 2026-09-11

### Added

- CRUD-Verwaltung für Modalitätsprofile mit referenzierten MWL- und Store-Zielen.
- Manueller kombinierter Modalitätscheck mit sicherer MWL-Abfrage, synthetischem C-STORE und getrennten Subresultaten.
- Diagnostische MWL-Wiederholung ohne Station AE bei null Treffern.
- Historientyp und Detaildarstellung für Modalitätsprüfungen.
- REST-Endpunkte, Alembic-Migration sowie Backend-, Frontend- und Browser-Tests für Modalitätsprofile.

### Changed

- Navigation um **Modalitäten** ergänzt und Produktversion auf 0.2.0 angehoben.
- Ein partieller Fehler ergibt konsistent ein fehlgeschlagenes Gesamtergebnis; erfolgreiche Subchecks bleiben einzeln sichtbar.

## [0.1.1] - 2026-09-11

### Added

- Echter lokaler MWL-C-FIND-Integrationstest für Pending-, Success-, Nulltreffer-, Reject-, Abort-, Failure- und Timeout-Pfade.
- SOP-spezifische Generatoren für Secondary Capture, CT, MR, Ultrasound, CR und DX.
- Zwei Full-Stack-Smoke-Tests vom Browser bis zu lokalen MWL- und Storage-SCPs.
- Eigener CI-Job für die Full-Stack-DICOM-Smoke-Tests.
- Komponentengetriebenes UI-System mit zentralen Design Tokens und wiederverwendbaren DICOM-Komponenten.
- Einstellungsseite für lokale UI- und DICOM-Standardwerte.

### Changed

- DICOM-Fehler unterscheiden TCP, Association Reject/Abort, Timeout, Presentation Context, C-FIND und Store-Status präziser.
- Synthetische Objekte enthalten SOP-spezifische typische Metadaten und bleiben eindeutig als nicht diagnostisch gekennzeichnet.
- Übersicht, Worklist, PACS Store, Ziele und Historie verwenden ein einheitliches On-Prem-Admin-Layout.
- PACS Store zeigt Transferfortschritt, technisches Log und Objektmetadaten kompakt an.

### Fixed

- C-STORE-Warnungen werden als angenommene Übertragung mit sichtbarer technischer Warnung behandelt.

## [0.1.0] - 2026-09-10

### Added

- Erste MVP-Version.
