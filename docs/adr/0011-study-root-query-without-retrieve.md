# ADR-0011: Study Root Query ohne Retrieve

Status: Accepted

## Context

Administratoren müssen prüfen können, ob gespeicherte Studien über den PACS-Query/Retrieve-Endpunkt auffindbar sind. C-MOVE oder C-GET erfordern zusätzlich einen Empfangsdienst und deutlich mehr Betriebs- und Sicherheitsentscheidungen.

## Decision

DCMSim 0.3.0 implementiert ausschließlich Study Root C-FIND auf Level `STUDY`. Mindestens ein Filter ist Pflicht. Ziele erhalten einen separaten Query/Retrieve-Port und Called AE. Antwort-Datasets bleiben flüchtig; die Historie persistiert keine Patientenresultate oder patientenbezogenen Filter.

## Consequences

+ Auffindbarkeit und Q/R-Freigabe lassen sich lokal diagnostizieren.
+ Kein Listener, eingehender Port oder zusätzlicher Prozess ist erforderlich.
- Bilder können noch nicht abgerufen werden.
