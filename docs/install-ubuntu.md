# Native Installation auf Ubuntu

Beispiel für Ubuntu 24.04, Python 3.12 und einen dedizierten Rechner im Kliniknetz. DCMSim bindet HTTP nur an `127.0.0.1:8080`; nginx übernimmt TLS und Anmeldung. Zertifikat, DNS-Name, Admin-Netz und Passwortrichtlinie an die Klinik anpassen. Vor dem ersten produktiven Start Datenbank- und Firewallpfade prüfen.

## Installation

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip nodejs npm nginx apache2-utils git
sudo useradd --system --home /var/lib/dcmsim --shell /usr/sbin/nologin dcmsim
sudo install -d -o dcmsim -g dcmsim -m 750 /opt/dcmsim /var/lib/dcmsim
sudo install -d -o root -g dcmsim -m 750 /etc/dcmsim
sudo -u dcmsim git clone https://github.com/ley338-gif/dcmsim.git /opt/dcmsim/current
cd /opt/dcmsim/current
sudo -u dcmsim python3.12 -m venv .venv
sudo -u dcmsim .venv/bin/pip install .
sudo -u dcmsim npm ci --prefix apps/web
sudo -u dcmsim npm run build --prefix apps/web
```

Ubuntu liefert Node.js je nach Paketquelle in einer älteren Version. Für den Build wird Node.js 22 benötigt; dessen freigegebene Klinik-Paketquelle verwenden und `node --version` vor `npm ci` prüfen.

`/etc/dcmsim/dcmsim.env` als root erstellen und mit `chmod 640`, Eigentümer `root:dcmsim`, schützen:

```text
DCMSIM_DATABASE_URL=sqlite:////var/lib/dcmsim/dcmsim.db
DCMSIM_STATIC_PATH=/opt/dcmsim/current/apps/web/dist
DCMSIM_PROXY_AUTH_ENABLED=true
DCMSIM_PROXY_AUTH_REQUIRED=true
DCMSIM_PROXY_USER_HEADER=X-Forwarded-User
DCMSIM_TRUSTED_PROXIES=127.0.0.1
DCMSIM_CONNECT_TIMEOUT=5
DCMSIM_ASSOCIATION_TIMEOUT=10
DCMSIM_DIMSE_TIMEOUT=20
DCMSIM_LOG_LEVEL=INFO
```

Die `.env.example` beschreibt weitere Werte. `DCMSIM_STATIC_PATH` zeigt auf das gebaute Frontend; die Docker-Installation verwendet weiter das im Image kopierte `app/static`.

```bash
sudo -u dcmsim sh -c 'set -a; . /etc/dcmsim/dcmsim.env; set +a; exec /opt/dcmsim/current/.venv/bin/alembic -c apps/api/alembic.ini upgrade head'
sudo cp /opt/dcmsim/current/deploy/dcmsim.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now dcmsim
```

Die Environment-Datei enthält ausschließlich vom Administrator geprüfte `DCMSIM_`-Zuweisungen. Sie wird für Migration und CheckMK als Shell-Datei eingelesen; keine unkontrollierten Werte darin ablegen.

## nginx und Zugang

`deploy/dcmsim.nginx.conf` an DNS-Namen und TLS-Zertifikat anpassen und nach `/etc/nginx/sites-available/dcmsim` kopieren. Das Beispiel nutzt nginx Basic Auth; das Passwort liegt ausschließlich bei nginx. `sudo htpasswd -c /etc/nginx/dcmsim.htpasswd adminname` erzeugt die erste Kennung; für weitere Kennungen `-c` weglassen. Die Datei auf `root:www-data` und Modus `640` setzen. Danach Symlink unter `sites-enabled` erstellen, `sudo nginx -t` und `sudo systemctl reload nginx` ausführen.

Für LDAP/AD kann nginx stattdessen `auth_request` zu einem vom Krankenhaus betriebenen Authentisierungsdienst verwenden. Dieser muss den verifizierten Benutzernamen liefern; nginx setzt daraus **immer selbst** `X-Forwarded-User` und überschreibt einen gleichnamigen Client-Header. Direkte Anfragen an Port 8080 dürfen das Kliniknetz nicht erreichen. Die systemd-Unit nutzt `--no-proxy-headers`, damit DCMSim die tatsächliche TCP-Quelladresse von nginx und keine vom Client gesetzten Forwarded-Header prüft.

Die Firewall erlaubt HTTPS nur aus dem Admin-Netz. Port 80 dient, falls gewünscht, allein der Weiterleitung auf HTTPS. DICOM-Verbindungen zu RIS/PACS gehen vom DCMSim-Host aus; Ziel-Firewall, Quell-IP und Calling AE müssen dort freigegeben sein.

## CheckMK

Endpoint unter **Systeme** bearbeiten, **Mit CheckMK überwachen** aktivieren und das Monitor Calling AE eintragen. Für MWL optional `HH:MM-HH:MM` und Mindestanzahl setzen; das Zeitfenster nutzt die lokale Serverzeit. Bei leerer Worklist außerhalb des Fensters bleibt der Dienst OK. Für STORE und QR wird C-ECHO geprüft, kein produktiver C-STORE.

Den CheckMK-Agenten nach Klinikstandard installieren; danach muss `/usr/lib/check_mk_agent/local/` existieren.

```bash
sudo install -m 755 /opt/dcmsim/current/deploy/dcmsim-check /usr/lib/check_mk_agent/local/dcmsim-check
sudo -u dcmsim sh -c 'set -a; . /etc/dcmsim/dcmsim.env; set +a; exec /opt/dcmsim/current/.venv/bin/dcmsim-check --all --report'
```

CheckMK ruft das Local Check Skript im Agentenzyklus auf. DCMSim plant selbst keine Prüfungen. Das Skript liest SQLite ohne Schreibzugriff, schreibt keine Historie und begrenzt die Gesamtlaufzeit auf 60 Sekunden. Nach Wartungen prüft `dcmsim-check --all --report` alle Endpoints; `--system RIS` und `--service MWL` filtern die Auswahl. Ein Beispiel: `47 von 48 OK, 0 WARN, 1 CRIT`.

## Update und Backup

Vor Änderungen ein konsistentes SQLite-Backup über **Einstellungen → Datensicherung** erstellen oder bei gestopptem Dienst die Datei `/var/lib/dcmsim/dcmsim.db` kopieren. Zusätzlich `/etc/dcmsim/dcmsim.env`, nginx-Konfiguration und Zertifikatsverwaltung sichern. Dann:

```bash
sudo systemctl stop dcmsim
cd /opt/dcmsim/current
sudo -u dcmsim git pull --ff-only
sudo -u dcmsim .venv/bin/pip install .
sudo -u dcmsim npm ci --prefix apps/web
sudo -u dcmsim npm run build --prefix apps/web
sudo -u dcmsim sh -c 'set -a; . /etc/dcmsim/dcmsim.env; set +a; exec .venv/bin/alembic -c apps/api/alembic.ini upgrade head'
sudo systemctl start dcmsim
sudo systemctl status dcmsim
```

Bei einem Restore den Dienst stoppen, gesicherte Datenbank mit Eigentümer `dcmsim:dcmsim` nach `/var/lib/dcmsim/dcmsim.db` zurücklegen und erst dann starten. Vor einem Versions-Rollback auch den zugehörigen Datenbankstand wiederherstellen. Der Docker-Weg bleibt im [README](../README.md) beschrieben.
