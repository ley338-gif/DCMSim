# ADR 0010: Sichere lokale Betriebsfunktionen

## Status

Akzeptiert

## Kontext

DCMSim benötigt portable Konfigurationen, Datenbanksicherungen und begrenzbare Historie, soll aber weder Scheduler noch eine zweite Persistenzschicht erhalten.

## Entscheidung

Konfigurationen werden als versioniertes JSON exportiert und namensbasiert importiert. Der Import löscht keine nicht enthaltenen Daten. Datenbankbackups verwenden SQLite Online Backup. Retention wird nach expliziter Bestätigung manuell ausgeführt.

## Konsequenzen

Alle Funktionen bleiben lokal und ohne Hintergrunddienst reproduzierbar. Ein Import kann bestehende gleichnamige Konfigurationen aktualisieren; dies wird in der Oberfläche transparent beschrieben.
