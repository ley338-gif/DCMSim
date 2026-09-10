# Changelog

Alle relevanten Änderungen werden nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) dokumentiert. Das Projekt verwendet Semantic Versioning.

## [Unreleased]

### Added

- Initialer DCMSim-MVP mit Zielverwaltung, Testhistorie und technischer Weboberfläche.
- Echte DICOM-C-ECHO-, MWL-C-FIND- und C-STORE-SCU-Implementierung.
- Synthetische Testobjekte für sechs SOP Classes sowie flüchtiger DICOM-Upload.
- Deterministische Worklist-Nulltreffer-Diagnose und klassifizierte DICOM-Fehler.
- Docker-Stack, Alembic-Schema, CI sowie Backend-, Frontend- und Browser-Tests.
- Komponentengetriebenes UI-System mit zentralen Design Tokens, AppShell, DICOM-Domänenkomponenten und interner Showcase-Seite.
- Einstellungsseite für lokale UI- und DICOM-Standardwerte.

### Changed

- Übersicht, Worklist, PACS Store, Ziele und Historie an das professionelle On-Prem-Admin-Layout angepasst.
- PACS-Store-Ablauf um Transferfortschritt, technisches Log und kompaktes Metadatenpanel erweitert.

### Fixed

### Removed

### Security

- Upload-Typ und -Größe werden begrenzt; Dateien werden ausschließlich im Speicher verarbeitet.

## [0.1.0] - 2026-09-10

### Added

- Erste MVP-Version.
