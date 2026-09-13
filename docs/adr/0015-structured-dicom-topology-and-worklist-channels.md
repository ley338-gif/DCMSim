# ADR 0015: Strukturierte DICOM-Topologie und Worklist-Kanäle

- **Status:** Akzeptiert
- **Datum:** 2026-09-13

## Kontext

DCMSim speicherte ein „Ziel“ als Kombination aus einem Host und je höchstens einer MWL-, STORE- und Query/Retrieve-Konfiguration. Modalitätsprofile referenzierten für Worklist und Storage jeweils eines dieser Ziele. Dieses Modell war für wenige Endpunkte einfach, führte aber bei realen KIS-/RIS-Installationen zu Mehrdeutigkeiten und Duplikaten: Dasselbe System kann mehrere Worklists über unterschiedliche Ports oder Called AE Titles anbieten, während mehrere Geräte dieselben technischen Endpunkte nutzen.

Eine rein flache Zielliste bietet außerdem keine verlässliche Orientierung nach Standort und Fachbereich. Ein beliebiger rekursiver Organisationsbaum, freie Systembeziehungen, Dokumente, Verantwortliche oder Audit-Funktionen würden DCMSim dagegen in Richtung einer vollständigen Registry verschieben.

Modality Worklist kann fachlich durch den angesprochenen Endpunkt sowie durch Matching Keys wie Scheduled Station AE Title und Modality getrennt werden. Eine automatische Wiederholung ohne diese einschränkenden Filter kann deshalb Ergebnisse anderer Geräte oder Bereiche liefern und unnötig patientenbezogene Daten anzeigen.

## Entscheidung

### Feste organisatorische Struktur

DCMSim verwendet ausschließlich die feste Hierarchie:

```text
Standort → Bereich → Modalitätsprofil
```

Ein Modalitätsprofil bildet ein Gerät oder einen bewusst benannten Gerätepool ab. Die Zuordnung zu einem Bereich ist optional. Nicht oder nicht mehr zugeordnete Profile bleiben sichtbar und werden unter **Nicht zugeordnet** dargestellt. Beim Löschen eines Bereichs wird kein Profil gelöscht.

### Getrennte technische Struktur

Die technische Konfiguration verwendet:

```text
DICOM-System → dienstspezifischer Endpoint
```

Ein DICOM-System ist die logische Gegenstelle, beispielsweise KIS/RIS oder PACS. Ein Endpoint ist eine konkrete Kombination aus Diensttyp (`MWL`, `STORE` oder `QR`), Host, Port und Called AE Title. Ein System darf mehrere Endpoints desselben Diensttyps besitzen. Dadurch kann beispielsweise ein KIS getrennte Worklists auf mehreren Ports abbilden, ohne als System dupliziert zu werden.

### Worklist-Kanal

Ein Worklist-Kanal verbindet einen optionalen Bereich und einen Modalitätstyp mit genau einem MWL-Endpoint. Er definiert unabhängig voneinander, wie die folgenden Matching Keys bestimmt werden:

- Scheduled Station AE Title: Wert des Modalitätsprofils, fester Wert oder nicht senden
- Modality: Wert des Modalitätsprofils, fester Wert oder nicht senden

Ein strukturiertes Modalitätsprofil referenziert seinen Worklist-Kanal und seinen STORE-Endpoint. Das Calling AE bleibt am Profil, weil DCMSim den Test aus Sicht dieses Geräts ausführt. Legacy-Referenzen bleiben während der Übergangszeit als kompatibler Fallback erhalten.

Der Worklist-Kanal ist ein internes Persistenz- und Kompatibilitätsmodell, kein eigener normaler UI-Arbeitsschritt. Das Modalitätsformular nimmt MWL-Endpoint und Filterregeln direkt entgegen. Die Orchestrierungs-API verwendet einen Kanal nur wieder, wenn Bereich, Modalität, Endpoint, beide Modi und beide festen Werte vollständig übereinstimmen; andernfalls erzeugt sie einen deterministisch benannten internen Kanal. Geteilte Kanäle werden nie für ein einzelnes Profil verändert oder umverdrahtet.

Migration `0007` ergänzt eine explizite interne Verwaltungsmarkierung. Bestehende und über Format v2 manuell verwaltete Kanäle erhalten den sicheren Standard `false`. Automatische Bereinigung löscht ausschließlich mit `true` markierte, nicht mehr referenzierte Kanäle. Namen allein begründen niemals Eigentum oder Löschbarkeit.

### Explizite breite Diagnose

Der normale Modalitätscheck sendet ausschließlich die im Kanal konfigurierten Matching Keys. Bei null Treffern erfolgt keine automatische breitere Abfrage.

Eine breitere Diagnose benötigt eine ausdrückliche Benutzeraktion. Sie behält den aktuellen Datumsfilter bei und entfernt nur Station AE und Modality. Die Oberfläche weist vor dem Auslösen darauf hin, dass dadurch mehr Worklist-Daten sichtbar werden können. Antwortdatensätze bleiben ausschließlich im aktuellen Browserzustand; die Historie speichert keine Worklist-Trefferlisten oder patientenbezogenen Filter.

### Migration und Kompatibilität

Migration `0006` führt Standorte, Bereiche, Systeme, Endpoints und Worklist-Kanäle ein.

- Jedes vorhandene Ziel wird mit derselben ID und demselben Namen in ein DICOM-System überführt.
- Für jeden aktivierten Legacy-Dienst wird ein dienstspezifischer Endpoint mit unverändertem Host, Port und Called AE erzeugt.
- Bestehende MWL-Profilreferenzen werden in nicht zugeordnete Worklist-Kanäle mit den bisherigen Abfrageregeln überführt.
- Bestehende STORE-Profilreferenzen werden auf den entsprechenden STORE-Endpoint abgebildet.
- Profile werden keiner organisatorischen Struktur zugeordnet; eine Zuordnung wird nicht aus Namen erraten.
- Legacy-Ziele, IDs und historische Snapshots bleiben bestehen, damit ältere Testläufe und Integrationen nicht umgedeutet werden.
- Der Konfigurationsexport verwendet Format 2. Der Import akzeptiert weiterhin Format 1 und normalisiert es in die neue Topologie. Importe bleiben nicht löschende Upserts und müssen vor der Ausführung bestätigt werden.

## Datenschutz- und Sicherheitsfolgen

Die neue Topologie speichert technische Infrastrukturbezeichner und optionale organisatorische Namen, aber keine Patientenstammdaten. Standort- und Bereichsnamen dürfen keine patientenbezogenen Informationen enthalten. Die vorhandene lokale Bereitstellung, die fehlende Cloud-Kommunikation und die datensparsame Historiengrenze bleiben unverändert.

Das explizite Auslösen breiter Worklist-Abfragen reduziert unbeabsichtigte Offenlegung gegenüber einer automatischen Diagnose. Es ersetzt keine Berechtigungsprüfung des KIS/RIS und keine Netzsegmentierung.

## Produktgrenze zu Healthcare Node Registry

Die feste Hierarchie dient ausschließlich der reproduzierbaren Auswahl und Diagnose von DICOM-Verbindungen. DCMSim bleibt ein leichtgewichtiges, lokales und nicht authentifiziertes Diagnosewerkzeug.

Frei modellierbare Organisationsebenen und Beziehungen, Mehrbenutzerbetrieb, Rollen, Audit, Dokumente, Verantwortliche, umfassende Systemstammdaten oder kontinuierliche Überwachung gehören weiterhin zum Healthcare Node Registry (HNR) oder benötigen eine ausdrücklich entworfene Integration. Diese Funktionen werden nicht schrittweise und unbemerkt in DCMSim nachgebaut.

## Konsequenzen

### Positiv

- Mehrere Worklists desselben KIS/RIS lassen sich ohne Systemduplikate abbilden.
- Modalitätsprüfungen zeigen die verwendeten Endpunkte und Matching-Regeln reproduzierbar an.
- Die feste Standort-/Bereichsstruktur verbessert die Orientierung, ohne eine allgemeine Registry einzuführen.
- Bestehende Installationen und historische Nachweise bleiben lesbar.
- Breite Worklist-Diagnosen werden bewusst und datensparsam ausgeführt.

### Negativ

- Das Datenmodell und der Konfigurationsimport werden umfangreicher.
- Legacy-Ziele müssen während einer Übergangszeit parallel unterstützt werden.
- Das Löschen verwendeter technischer Endpoints muss eingeschränkt oder vorher entkoppelt werden.
- Organisatorische Auswertungen historischer Testläufe sind nicht automatisch rückwirkend möglich, weil keine erfundene Standortzuordnung in alte Snapshots geschrieben wird.

## Verworfene Alternativen

### Strikter Baum mit Zielen als Blätter

Verworfen, weil zentrale PACS-/RIS-Systeme mehreren Bereichen und Geräten dienen und andernfalls dupliziert werden müssten.

### Freie Tags

Verworfen als primäre Struktur, weil Schreibvarianten und uneindeutige Zuordnungen keine zuverlässige Navigation ergeben.

### Beliebiger rekursiver Organisations- oder Beziehungsgraph

Verworfen, weil dies die Produktgrenze zu HNR überschreiten und den lokalen Diagnosezweck unnötig verkomplizieren würde.
