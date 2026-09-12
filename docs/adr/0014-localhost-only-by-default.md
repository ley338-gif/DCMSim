# ADR-0014: Docker-Port nur lokal veröffentlichen

Status: Accepted

## Kontext

DCMSim hat im MVP keine Benutzeranmeldung und kann DICOM-Endpunkte kontaktieren sowie lokale Konfigurationen und Testhistorie anzeigen. Eine Portveröffentlichung auf allen Host-Schnittstellen macht diese Funktionen ohne weitere Schutzschicht im Netzwerk erreichbar.

## Entscheidung

Docker Compose bindet Port 8080 standardmäßig ausschließlich an `127.0.0.1` des Host-Rechners. Für bewusst abgesicherten Netzwerkzugriff kann `DCMSIM_PUBLISH_HOST` auf eine private Host-Adresse gesetzt werden. Das ist eine Opt-in-Betriebsentscheidung und ersetzt keine Authentifizierung oder Netzwerkzugangskontrolle.

## Folgen

- Der lokale Start unter `http://localhost:8080` bleibt unverändert.
- Andere Geräte können die Standardinstallation nicht direkt erreichen.
- Bestehende Netzwerkzugriffe brauchen eine explizite Konfigurationsanpassung oder einen abgesicherten Reverse Proxy beziehungsweise Tunnel.
