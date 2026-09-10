# DCMSim Benutzerhandbuch

## 1. Einführung

DCMSim prüft aus Sicht einer Modalität, ob ein Worklist- oder PACS-Endpunkt erreichbar und korrekt konfiguriert ist. Es ist ein Diagnosewerkzeug, kein klinischer Viewer.

## 2. Begriffe

- **Calling AE** ist der Name, mit dem DCMSim auftritt; **Called AE** ist der konfigurierte Name der Gegenstelle.
- **MWL SCU** (DCMSim) fragt per **C-FIND** einen **MWL SCP** (RIS/PACS) ab.
- **Storage SCU** (DCMSim) sendet per C-STORE an einen **Storage SCP** (PACS).
- Eine **SOP Class** bezeichnet den DICOM-Objekttyp. Eine **Transfer Syntax** bestimmt seine Kodierung. Beide werden im **Presentation Context** ausgehandelt.
- **Study UID**, **Series UID** und **SOP UID** identifizieren Untersuchung, Serie und einzelnes Objekt weltweit eindeutig.

## 3. Ziele verwalten

Unter **Ziele** Name und Host eintragen, benötigte Dienste aktivieren sowie Port, Called AE und Default Calling AE setzen. Gespeicherte Ziele erscheinen in den Testformularen; manuelle Eingabe bleibt immer möglich.

## 4. Worklist testen

Endpunkt auswählen oder manuell eingeben. Datum ist auf heute vorbelegt. Modalität, Station AE, Patient ID, Accession Number und Patient Name sind optional. **Worklist abfragen** startet die Association und C-FIND.

## 5. Broad Query verwenden

**Broad Query** sendet Rückgabeschlüssel ohne einschränkende Filter. Damit lässt sich prüfen, ob die Worklist grundsätzlich Daten liefert.

## 6. Worklist-Ergebnisse interpretieren

Die Ergebniszeile trennt TCP, Association, C-FIND, Dauer und Trefferzahl. Ein Tabellenklick öffnet das komplette DICOM Dataset inklusive Scheduled Procedure Step Sequence. Bei null Treffern zeigen Schnellaktionen, ob Station AE oder Modalität zu restriktiv war.

## 7. PACS Store testen

Unter **PACS Store** Endpunkt, SOP Class und Transfer Syntax wählen. **C-STORE senden** zeigt ausgehandelten Ablauf, Statuscode und UIDs.

## 8. Synthetisches DICOM-Testobjekt

Der Standard erzeugt `DCMSIM^TEST`, neue UIDs und ein Pixelbild mit „NOT FOR DIAGNOSTIC USE“. Diese Daten sind nicht klinisch.

## 9. Eigene DICOM-Datei senden

Auf **Eigene DICOM-Datei** wechseln und `.dcm`/`.dicom` wählen. Achtung: Sie kann echte Patientendaten enthalten. Die Datei wird nur für den Request im Speicher gehalten und nicht persistiert.

## 10. Historie

Die Historie zeigt Zeitpunkt, Typ, Ziel, Ergebnis und Dauer. Typ, Status und Freitext können gefiltert werden. Ein Eintrag öffnet Testparameter, Result Summary, technisches Log und die gespeicherten Request-/Response-Daten.

## 11. Technische Details anzeigen

Aufklappbare Bereiche enthalten Filter, DICOM-Tags, UIDs, Status und Fehlerdetails. Monospace-Felder sind direkt für den Abgleich mit PACS/RIS-Konfigurationen gedacht.

## 12. Häufige Fehler

`DICOM_CONNECTION_FAILED` deutet auf Host, Port oder Netzwerk hin. `DICOM_ASSOCIATION_REJECTED` verlangt Prüfung der AE Titles und Freischaltung. `DICOM_NO_PRESENTATION_CONTEXT` bedeutet, dass SOP Class und Transfer Syntax nicht akzeptiert wurden. Weitere Schritte: [Troubleshooting](troubleshooting.md).

## 13. Einstellungen

Unter **Einstellungen** lassen sich lokale Benutzerstandards für Calling AE, Timeouts, Logging, Retention und Darstellung vormerken. Serverseitige Timeouts und Log Level werden im MVP weiterhin über die Container-Umgebung konfiguriert; die Oberfläche weist darauf ausdrücklich hin.
