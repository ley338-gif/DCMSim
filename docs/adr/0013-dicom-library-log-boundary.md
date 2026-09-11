# ADR-0013: Datenschutzgrenze für DICOM-Bibliothekslogs

## Status

Accepted

## Context

pynetdicom protokolliert auf INFO und DEBUG vollständige C-FIND-Datasets. Diese können Patientenname, Patient-ID, Geburtsdatum und Accession Number enthalten. Der globale DCMSim-Log-Level darf daher nicht ungefiltert an DICOM-Abhängigkeiten vererbt werden.

## Decision

DCMSim konfiguriert den Root-Logger mit dem gewünschten Application Log Level, setzt die Logger `pydicom` und `pynetdicom` jedoch mindestens auf `WARNING`. Eigene Abschlussereignisse enthalten ausschließlich Endpunkt, AE Titles, Dauer, Erfolg und technische Fehlerklasse. Vollständige DICOM-Antworten werden nur kontrolliert an den aktuellen Browser geliefert.

## Consequences

Container-Logs bleiben für Betrieb und Fehlerklassifikation nutzbar, enthalten aber keine regulären Dataset-Dumps. Eine tiefere Protokollanalyse erfolgt über die technische Ansicht im laufenden Test oder über ein kontrolliertes externes DICOM-Tracing, nicht durch globales Aktivieren von Bibliotheks-DEBUG-Logs.
