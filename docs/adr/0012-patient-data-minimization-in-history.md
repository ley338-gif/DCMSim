# ADR-0012: Patientendaten-Minimierung in der Testhistorie

## Status

Accepted

## Context

Worklist- und PACS-Suchergebnisse sowie hochgeladene DICOM-Dateien können echte Patientenidentifikatoren enthalten. Für die unmittelbare Diagnose müssen diese Angaben im aktuellen Browser sichtbar sein. Für die langfristige technische Historie reichen Status, Dauer, Trefferzahl, Endpunkt und ausgehandelte DICOM-Parameter.

## Decision

Eine zentrale Schutzgrenze im Historienservice entfernt vor der Persistenz Trefferlisten und Suchfilter aus `mwl_find` und `qr_find` sowie Patientenname und Patient-ID aus `dicom_store`. Technische UIDs bleiben erhalten, weil sie die Zuordnung eines C-STORE-Vorgangs ermöglichen. Migration `0004` entfernt dieselben Felder aus bestehenden Einträgen; ihr Downgrade stellt gelöschte Patientendaten nicht wieder her.

## Consequences

Patientenbezogene DICOM-Antworten sind nur während des aktuellen Requests verfügbar. Ein späterer Historienaufruf zeigt weiterhin den technischen Verlauf, kann aber keine Worklist- oder Patientenansicht rekonstruieren. Die Regel gilt zentral für alle Aufrufer von `record_run` und schützt damit auch künftige Routen desselben Testtyps.
