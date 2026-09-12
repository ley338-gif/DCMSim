# DCMSim Benutzerhandbuch

## 1. Einführung

DCMSim prüft aus Sicht einer Modalität, ob ein Worklist- oder PACS-Endpunkt erreichbar und korrekt konfiguriert ist. Es ist ein Diagnosewerkzeug, kein klinischer Viewer.

Die **Übersicht** führt direkt zu Worklist, PACS Store und PACS-Suche. Sie zeigt alle konfigurierten Dienste sowie die Verteilung und die letzten Ergebnisse von Worklist-, Store-, Query/Retrieve- und Modalitätsprüfungen.

„Tests heute“ und Erfolgsquote beziehen sich auf den lokalen Kalendertag des Browsers; die Testverteilung zählt alle gespeicherten Läufe. Die Tabelle zeigt dagegen bewusst nur die jüngsten Tests. Die Kennzahlen sind keine automatische DICOM-Überwachung.

Zeitpunkte in Übersicht und Historie werden aus eindeutig gekennzeichneten UTC-Zeitstempeln in die lokale Browserzeit umgerechnet. Die Datumsfilter für Worklist und PACS-Suche sind beim Öffnen mit dem lokalen heutigen Datum vorbelegt und können jederzeit geändert werden.

Über **Hilfe** in der Kopfzeile öffnet sich der integrierte Schnellstart mit Erläuterungen zu Zielstatus, Fehlerdiagnose, Datenschutz und unterstützten DICOM-Diensten. **Test-Historie** führt direkt zu den bisherigen Testläufen. Der Hinweis **Ohne Anmeldung** ist wichtig: DCMSim besitzt im MVP keine Benutzerkonten und darf nur in einem vertrauenswürdigen internen Netz betrieben werden.

Beim Docker-Start ist Port 8080 standardmäßig nur auf `127.0.0.1` des Host-Rechners erreichbar. Ein Zugriff aus dem Netzwerk erfordert eine bewusste Anpassung von `DCMSIM_PUBLISH_HOST` und eine geeignete Zugangssicherung durch die Infrastruktur; DCMSim selbst bietet keine Anmeldung.

Diese Einschränkung betrifft nur eingehende Aufrufe der Oberfläche. DICOM-Tests verbinden sich weiterhin ausgehend mit den konfigurierten Zielen. Bei Docker bezeichnet `127.0.0.1` als DICOM-Ziel den DCMSim-Container selbst; für PACS/RIS auf dem Host oder im Netzwerk eine vom Container erreichbare Adresse verwenden.

Docker zeigt den Container als gesund an, wenn Webdienst und lokale Datenbank antworten. Das prüft keine DICOM-Gegenstelle. Deren Erreichbarkeit wird erst durch einen ausdrücklich gestarteten Test wie C-ECHO geprüft.

## 2. Begriffe

- **Calling AE** ist der Name, mit dem DCMSim auftritt; **Called AE** ist der konfigurierte Name der Gegenstelle.
- **MWL SCU** (DCMSim) fragt per **C-FIND** einen **MWL SCP** (RIS/PACS) ab.
- **Storage SCU** (DCMSim) sendet per C-STORE an einen **Storage SCP** (PACS).
- **Query/Retrieve SCU** sucht per Study Root C-FIND nach Studien. Es ruft keine Bilder ab.
- Eine **SOP Class** bezeichnet den DICOM-Objekttyp. Eine **Transfer Syntax** bestimmt seine Kodierung. Beide werden im **Presentation Context** ausgehandelt.
- **Study UID**, **Series UID** und **SOP UID** identifizieren Untersuchung, Serie und einzelnes Objekt weltweit eindeutig.

## 3. Ziele verwalten

Unter **Ziele** Name und Host eintragen, benötigte Dienste aktivieren sowie Port, Called AE und Default Calling AE setzen. Worklist, Store und PACS-Suche können unterschiedliche Ports oder Called AEs verwenden. Gespeicherte Ziele erscheinen in den Testformularen; manuelle Eingabe bleibt immer möglich.

Der Zielstatus zeigt den letzten direkt zugeordneten Einzeltest mit Ergebnis und Zeitpunkt. Ohne einen solchen Lauf steht dort **Ungeprüft**. Ein gespeichertes Ziel kann über **Bearbeiten → Verbindung testen** gezielt geprüft werden. Eine kombinierte Modalitätsprüfung kann unterschiedliche Ziele verwenden und wird deshalb weiterhin separat in der Historie dargestellt.

Wenn Host, verwendeter Dienst-Port, Called AE, Default Calling AE oder der verwendete Dienst seit dem Test geändert wurden, erscheint **Erneut prüfen** statt eines veralteten Erfolgs oder Fehlers. Eine reine Namensänderung ändert den technischen Prüfstatus nicht. Bei älteren Tests ohne gespeicherte Ziel-Momentaufnahme steht **Nicht belegbar**; nach einem neuen Einzeltest erscheint wieder ein aktuelles Ergebnis.

## 4. Worklist testen

Endpunkt auswählen oder manuell eingeben. Datum ist auf heute vorbelegt. Modalität, Station AE, Patient ID, Accession Number und Patient Name sind optional. **Worklist abfragen** startet die Association und C-FIND.

## 5. Broad Query verwenden

**Broad Query** sendet Rückgabeschlüssel ohne einschränkende Filter. Damit lässt sich prüfen, ob die Worklist grundsätzlich Daten liefert.

## 6. Worklist-Ergebnisse interpretieren

Die Ergebniszeile trennt TCP, Association, C-FIND, Dauer und Trefferzahl. Ein Tabellenklick öffnet das komplette DICOM Dataset inklusive Scheduled Procedure Step Sequence. Bei null Treffern zeigen Schnellaktionen, ob Station AE oder Modalität zu restriktiv war.

Worklist-Treffer und verwendete Suchfilter sind nur in der unmittelbaren Antwort sichtbar. Die Historie speichert davon ausschließlich technische Kennzahlen wie Status, Dauer und Trefferzahl.

## 7. PACS Store testen

Unter **PACS Store** Endpunkt, SOP Class und Transfer Syntax wählen. **C-STORE senden** zeigt ausgehandelten Ablauf, Statuscode und UIDs.

## 8. Synthetisches DICOM-Testobjekt

Der Standard erzeugt `DCMSIM^TEST`, neue UIDs und ein Pixelbild mit „NOT FOR DIAGNOSTIC USE“. Diese Daten sind nicht klinisch.

## 9. Eigene DICOM-Datei senden

Auf **Eigene DICOM-Datei** wechseln und `.dcm`/`.dicom` wählen. Achtung: Sie kann echte Patientendaten enthalten. Die Datei wird nur für den Request im Speicher gehalten und nicht persistiert.

Patientenname und Patient-ID aus der Datei erscheinen während des aktuellen Tests in der Metadatenansicht, werden aber nicht in der Testhistorie gespeichert.

## 10. Modalitätsprofile

Unter **Modalitäten** bildet ein Profil die Konfiguration eines Geräts ab. **Neue Modalität** öffnen, Name, Modalitätscode und Calling AE eintragen und die benötigten Dienste aktivieren. MWL- und Store-Ziel werden aus den bereits unter **Ziele** gepflegten Systemen gewählt; Called AE, Host und Port bleiben deshalb zentral am Ziel gespeichert.

Unterstützt werden zunächst CT, MR, US, CR, DX, OT, XA, MG, NM und PT. Ein Profil kann nur gespeichert werden, wenn mindestens ein Dienst aktiv ist und jeder aktive Dienst ein passendes Ziel besitzt.

## 11. Modalität prüfen

**Modalität prüfen** führt die aktivierten Subchecks nacheinander aus. Worklist fragt zunächst heutiges Datum, Profil-Modalität und Calling AE als Station AE ab. Bei null Treffern testet DCMSim zusätzlich ohne Station AE und zeigt beide Trefferzahlen als technische Beobachtung. Das ist keine Aussage über eine fehlerhafte RIS-Konfiguration.

Der Store-Check erzeugt ein synthetisches Objekt. CT, MR, US, CR und DX verwenden die entsprechende Storage SOP Class; andere Profilmodalitäten verwenden sichtbar gekennzeichnet Secondary Capture. Standard ist Explicit VR Little Endian.

**PASS** bedeutet, dass alle aktivierten Subchecks erfolgreich waren. Schlägt Worklist oder Store fehl, lautet das Gesamtergebnis **FAIL**, während der erfolgreiche Teil weiterhin separat sichtbar bleibt. So ist beispielsweise „Worklist funktioniert, Store nicht“ direkt erkennbar. Unter **Technische Details** stehen Statuscodes, Schritte, SOP Class, Transfer Syntax und die diagnostische Wiederholung.

Während des Checks kann die Browseranzeige abgebrochen werden. Der bereits gestartete DICOM-Vorgang kann serverseitig noch regulär enden und in der Historie erscheinen. **Erneut prüfen** wiederholt den letzten Check mit demselben Profil. Fehlerresultate enthalten einen empfohlenen nächsten Diagnoseschritt.

## 12. PACS-Studien suchen

Unter **PACS-Suche** einen Query/Retrieve-Endpunkt auswählen und mindestens ein Kriterium verwenden. Das heutige Studiendatum ist sicher vorbelegt; alternativ sind Patientenname, Patient ID, Accession Number und Modalität möglich. **Studien suchen** führt Study Root C-FIND auf Level `STUDY` aus. Ein Klick auf eine Zeile öffnet die vollständige DICOM-Antwort. DCMSim führt dabei weder C-MOVE noch C-GET aus.

Patienten- und Studiendaten werden nur in der aktuellen Antwort angezeigt. Die Historie speichert für diesen Test lediglich technischen Status, Dauer und Trefferzahl.

## 13. Historie

Die Historie zeigt Zeitpunkt, Typ, Ziel, Ergebnis und Dauer. Typ, Status und Freitext können gefiltert werden. Ein Eintrag öffnet Testparameter, Result Summary, technisches Log und die gespeicherten Request-/Response-Daten.

Seit Version 0.3.7 speichert jeder neue Einzeltest die beim Test tatsächlich verwendeten technischen Zielangaben (Name, Host, Port und AE-Titel). Änderungen an einem gespeicherten Ziel verändern frühere Historieneinträge nicht. Bei älteren Einträgen ohne diese Momentaufnahme können technische Felder fehlen; fehlende Werte werden nicht aus der heutigen Zielkonfiguration rekonstruiert.

Filter und Freitextsuche werden serverseitig ausgeführt. Die Ansicht zeigt 50 Einträge pro Seite und bleibt dadurch auch bei einer längeren lokalen Nutzung übersichtlich. **CSV exportieren** lädt genau die aktuell gefilterten technischen Historienfelder herunter. Der Export enthält keine Worklist- oder PACS-Trefferlisten und keine patientenbezogenen Suchfilter.

Der Typ **Modalitätsprüfung** speichert Profilname und beide Subresultate in einem gemeinsamen Lauf. Worklist-Ergebnislisten mit Patientendaten werden dabei nicht in diesen kombinierten Historieneintrag kopiert.

## 14. Technische Details anzeigen

Aufklappbare Bereiche enthalten Filter, DICOM-Tags, UIDs, Status und Fehlerdetails. Monospace-Felder sind direkt für den Abgleich mit PACS/RIS-Konfigurationen gedacht.

## 15. Häufige Fehler

`TCP_CONNECTION_FAILED` deutet auf Host, Port oder Netzwerk hin. `DICOM_ASSOCIATION_REJECTED` verlangt Prüfung der AE Titles und Freischaltung. `DICOM_ASSOCIATION_ABORTED` bezeichnet einen Abbruch der Association. `DICOM_TIMEOUT` bedeutet, dass innerhalb der Frist keine finale Antwort kam. `DICOM_NO_PRESENTATION_CONTEXT` bedeutet, dass SOP Class und Transfer Syntax nicht akzeptiert wurden. Weitere Schritte: [Troubleshooting](troubleshooting.md).

## 16. Einstellungen

Unter **Einstellungen** lassen sich lokale Benutzerstandards für Calling AE, Timeouts, Logging, Retention und Darstellung verwalten. Das gespeicherte Default Calling AE wird bei neuen manuellen DICOM-Tests, Zielen und Modalitätsprofilen vorbelegt. Die kompakte Tabellenansicht wird nach dem Speichern sofort und bei späteren Aufrufen automatisch verwendet. Serverseitige Timeouts und Log Level werden im MVP weiterhin über die Container-Umgebung konfiguriert; die Oberfläche weist darauf ausdrücklich hin.

Unter **Datensicherung** kann die Konfiguration als JSON exportiert und wieder importiert werden. Der Import aktualisiert Einträge gleichen Namens oder legt neue an; nicht enthaltene Daten werden nicht gelöscht. Das SQLite-Backup ist eine konsistente Kopie der gesamten lokalen Datenbank. Unter **Retention** werden Einträge älter als die gewählte Tageszahl nach Bestätigung manuell gelöscht.
