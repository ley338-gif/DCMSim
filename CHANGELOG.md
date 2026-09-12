# Changelog

Alle relevanten Änderungen werden nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) dokumentiert. Das Projekt verwendet Semantic Versioning.

## [Unreleased]

### Added

- Noch keine Änderungen.

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
