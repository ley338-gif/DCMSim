# Troubleshooting

## Worklist liefert 0 Treffer

1. Broad Query ausführen.
2. Station AE entfernen.
3. Modalität entfernen.
4. Datum und Zeitzone kontrollieren.
5. Raw Dataset und RIS-/MWL-Mapping prüfen.

Liefert Broad Query Treffer, funktionieren Netzwerk und DICOM grundsätzlich; ein Query-Filter oder Mapping ist wahrscheinlich die Ursache.

## Association rejected / Called AE falsch

Called AE exakt mit der SCP-Konfiguration vergleichen (maximal 16 Zeichen). Calling AE und Quell-IP im PACS/RIS freischalten. Eine TCP-Verbindung allein bestätigt diese Konfiguration nicht.

## Station AE, Datum oder Modalität falsch

Station AE ist häufig modalitätsspezifisch. Ohne diesen Filter erneut testen. DICOM-Datum verwendet `YYYYMMDD`; DCMSim übernimmt die Umwandlung. Modalitätscode wie `CT`, `MR`, `US`, `CR` oder `DX` mit dem RIS-Mapping abgleichen.

## PACS Store schlägt fehl / No Presentation Context

Prüfen, ob die gewählte SOP Class am PACS freigegeben ist. Danach zwischen Explicit und Implicit VR Little Endian wechseln. „No Acceptable Presentation Context“ ist eine Aushandlungsablehnung vor C-STORE, kein Bildfehler.

## Worklist funktioniert, Store nicht

Das MWL-Ziel ist erreichbar und akzeptiert C-FIND; daraus folgt nicht, dass der Storage-Dienst dieselbe Freischaltung besitzt. Store Called AE und Port, Freigabe der Calling AE und Quell-IP sowie akzeptierte SOP Class und Transfer Syntax am PACS prüfen.

## Store funktioniert, Worklist nicht

Die Storage-Freigabe bestätigt nur C-STORE. MWL Called AE und Port sowie die C-FIND-Freigabe separat prüfen. Wenn die Association funktioniert, Query zunächst ohne Station AE und anschließend ohne weitere Filter vergleichen.

## Station AE liefert keine Treffer

Zeigt der automatische Versuch ohne Station AE Treffer, ist die Worklist grundsätzlich erreichbar. Schreibweise und Mapping des Profil-Calling-AE mit der Scheduled Station AE im RIS vergleichen. DCMSim bewertet dies bewusst nur als Beobachtung.

## SOP Class oder Transfer Syntax nicht akzeptiert

`DICOM_NO_PRESENTATION_CONTEXT` bedeutet, dass die Gegenstelle die konkrete Kombination nicht angenommen hat. Zuerst SOP-Class-Freigabe prüfen, dann Explicit gegen Implicit VR Little Endian testen. Bei Modalitäten ohne eigenen Generator verwendet der kombinierte Check transparent Secondary Capture.

## C-STORE Status ungleich 0x0000

`0xBxxx` ist eine Warnung; das PACS kann das Objekt angenommen und verändert haben. `0xAxxx`/`0xCxxx` ist ein Fehler. Statuscode mit der Herstellerdokumentation abgleichen.

## Timeout

Firewall, Routing, falschen Port und Antwortzeit der Gegenstelle prüfen. DCMSim begrenzt Connect-, Association- und DIMSE-Wartezeiten, damit Tests nicht hängen.

## PACS erreichbar, Bild aber nicht auffindbar

Study-, Series- und SOP-UID aus dem Testergebnis kopieren und im PACS-Log suchen. Patient ID beginnt mit `DCMSIM-`; Study Description ist `PACS STORE TEST`. Importregeln, Quarantäne und Modalitätsfilter des PACS prüfen.
