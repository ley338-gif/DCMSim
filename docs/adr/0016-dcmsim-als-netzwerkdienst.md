# ADR 0016: DCMSim als Netzwerkdienst

- **Status:** Akzeptiert; ersetzt ADR-0004 und ändert die Produktgrenze aus ADR-0010, 0014 und 0015
- **Datum:** 2026-10-12

## Kontext

DCMSim wird dauerhaft auf einer eigenen Ubuntu-Maschine im Kliniknetz betrieben. Ein RIS kann je Fachabteilung einen eigenen MWL-Port bereitstellen. Manuelle Einzeltests allein reichen für die Betriebsüberwachung nicht. HNR übernimmt diese Aufgabe in der Praxis nicht.

## Entscheidung

DCMSim übernimmt die Anmeldung über einen vorgeschalteten Reverse Proxy, die Zuordnung manueller Tests zu einem Proxy-Benutzernamen und die technische Überwachung von DICOM-Endpoints. Der Webdienst vertraut einem konfigurierbaren Identitätsheader ausschließlich von konfigurierten Proxy-IP-Adressen. Die Pflicht zur Anmeldung ist für lokale Entwicklung abschaltbar; im Kliniknetz wird sie eingeschaltet. DCMSim speichert keine Passwörter und verwaltet weder Benutzer noch Rollen.

CheckMK steuert den Prüfablauf und die Alarmierung. Ein separater, kurzlebiger Local Check liest die Endpoint-Konfiguration aus SQLite und prüft MWL per C-FIND sowie STORE/QR per C-ECHO. Die Web-App enthält keinen Scheduler, Worker oder Hintergrunddienst. Monitorprüfungen schreiben keine Historie. Das Calling AE für diese unabhängige Prüfung wird pro Endpoint gespeichert; Profil-Calling-AEs bleiben unverändert. Ein optionales lokales Zeitfenster mit Mindesttrefferzahl kann leere Worklists als WARN kennzeichnen. Ohne solche Plausibilitätsregel ist eine leere Worklist OK.

Bei HNR bleiben Dokumente, frei modellierbare Beziehungen und organisationsweite Stammdaten. Die feste DCMSim-Topologie bleibt auf DICOM-Diagnose beschränkt.

## Folgen und Alternativen

Die Datenbank erhält eine additive Migration für Benutzerzuordnung und Monitor-Konfiguration. Bestehende Tests behalten `NULL` als Benutzer; alte Exporte bleiben importierbar. Patientendaten bleiben nach ADR-0012 aus Historie, Logs und CheckMK-Ausgabe ausgeschlossen. Die Anmeldung setzt eine korrekt konfigurierte Proxy-Grenze voraus: Backend nur auf Loopback, Identitätsheader am Proxy überschreiben, TLS und Netzfilter verwenden.

Ein im Webdienst laufender Scheduler wurde verworfen, weil CheckMK bereits Ablauf, Ausfälle und Benachrichtigung übernimmt. Ein automatischer Ende-zu-Ende-Storage-Test ins produktive PACS bleibt ein möglicher nächster Schritt; er erfordert einen abgestimmten Testpatienten und eine Löschregel mit dem PACS-Hersteller.

## Arbeitsphasen

1. Produktgrenze und Betriebsdokumentation berichtigen.
2. Migration, Proxy-Identität, Historie und Konfigurationsformat implementieren.
3. Kurzlebigen Monitor mit begrenzter Laufzeit und echten DICOM-Tests ergänzen.
4. Oberfläche, Ubuntu-Beispiele und Qualitätssicherung abschließen.
