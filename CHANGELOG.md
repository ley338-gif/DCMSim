# Changelog

Alle relevanten Änderungen werden nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) dokumentiert. Das Projekt verwendet Semantic Versioning.

## [Unreleased]

### Added

- Noch keine Änderungen.

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
