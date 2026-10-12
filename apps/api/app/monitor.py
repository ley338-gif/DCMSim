"""Short-lived CheckMK local check; no web service or history writes."""

import argparse
import json
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from time import monotonic

from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.logging import configure_logging
from app.dicom.datasets import build_mwl_query
from app.dicom.errors import DicomError
from app.dicom.network import echo, find_worklist
from app.services.diagnostics import recommendation_for


def load_endpoints(*, include_all: bool, system: str | None, service: str | None) -> list[dict]:
    url = make_url(settings.database_url)
    if url.drivername != "sqlite" or not url.database or url.database == ":memory:":
        raise ValueError("Monitor benötigt eine SQLite-Datei")
    path = Path(url.database).resolve()
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=1) as db:
        db.execute("PRAGMA query_only=ON")
        rows = db.execute(
            "SELECT e.id, s.name, e.name, e.service, e.host, e.port, e.called_ae, "
            "e.monitored, e.monitor_calling_ae, e.monitor_window, e.monitor_min_count "
            "FROM dicom_endpoints e JOIN dicom_systems s ON s.id=e.system_id "
            "ORDER BY s.name, e.name"
        ).fetchall()
    keys = ("id", "system", "name", "service", "host", "port", "called_ae", "monitored", "calling_ae", "window", "min_count")
    return [
        dict(zip(keys, row, strict=True))
        for row in rows
        if (include_all or row[7]) and (system is None or row[1] == system) and (service is None or row[3] == service)
    ]


def window_active(window: str | None, now: datetime | None = None) -> bool:
    if not window:
        return False
    start, end = window.split("-")
    current = (now or datetime.now().astimezone()).strftime("%H:%M")
    return start <= current < end if start < end else current >= start or current < end


def check_endpoint(endpoint: dict, now: datetime | None = None) -> dict:
    started = monotonic()
    network_endpoint = {
        "host": endpoint["host"], "port": endpoint["port"],
        "called_ae": endpoint["called_ae"], "calling_ae": endpoint["calling_ae"],
    }
    try:
        if endpoint["service"] == "MWL":
            # Date limits the request; no matching key contains a patient identifier.
            query = build_mwl_query({"date": (now or datetime.now().astimezone()).date()})
            result = find_worklist(network_endpoint, query, count_only=True)
            count = result["count"]
        else:
            result = echo(network_endpoint)
            count = 0
        if not result["success"]:
            code = "DICOM_C_ECHO_FAILED"
            return {"state": 2, "count": count, "duration_ms": result["duration_ms"], "message": f"{code}: {recommendation_for(code)}"}
        if endpoint["service"] == "MWL" and window_active(endpoint["window"], now) and count < endpoint["min_count"]:
            return {"state": 1, "count": count, "duration_ms": result["duration_ms"], "message": f"Worklist unter Mindestanzahl {endpoint['min_count']}; RIS-Zuordnung und Arbeitszeitfenster prüfen."}
        return {"state": 0, "count": count, "duration_ms": result["duration_ms"], "message": "DICOM-Prüfung erfolgreich"}
    except DicomError as exc:
        return {"state": 2, "count": 0, "duration_ms": round((monotonic() - started) * 1000), "message": f"{exc.code}: {recommendation_for(exc.code) or 'DICOM-Gegenstelle prüfen.'}"}
    except Exception:
        return {"state": 2, "count": 0, "duration_ms": round((monotonic() - started) * 1000), "message": "MONITOR_INTERNAL_ERROR: Monitorkonfiguration und Dienstprotokoll prüfen."}


def _worker(endpoint: dict, timeout: float) -> dict:
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "app.monitor", "--worker"],
            input=json.dumps(endpoint), text=True, capture_output=True, timeout=max(0.1, timeout), check=True,
        )
        result = json.loads(completed.stdout)
        if not isinstance(result, dict) or result.get("state") not in (0, 1, 2):
            raise ValueError("Invalid worker response")
        return result
    except subprocess.TimeoutExpired:
        return {"state": 2, "count": 0, "duration_ms": round(timeout * 1000), "message": "DICOM_TIMEOUT: " + (recommendation_for("DICOM_TIMEOUT") or "Gegenstelle prüfen.")}
    except Exception:
        return {"state": 2, "count": 0, "duration_ms": 0, "message": "MONITOR_INTERNAL_ERROR: Monitorinstallation und Dienstprotokoll prüfen."}


def run_checks(endpoints: list[dict], *, timeout: float = 60, jobs: int = 4, per_endpoint_timeout: float = 25) -> list[dict]:
    deadline = monotonic() + timeout

    def run_one(endpoint: dict) -> dict:
        remaining = deadline - monotonic()
        if remaining <= 0:
            return {"state": 2, "count": 0, "duration_ms": 0, "message": "DICOM_TIMEOUT: Gesamtlaufzeit erreicht; Gegenstelle prüfen."}
        return _worker(endpoint, min(remaining, per_endpoint_timeout))

    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = [executor.submit(run_one, endpoint) for endpoint in endpoints]
        return [future.result() for future in futures]


def _safe(value: object) -> str:
    return " ".join(str(value).replace('"', "'").replace("|", "/").split())


def local_check_line(endpoint: dict, result: dict) -> str:
    name = _safe(f"DCMSim {endpoint['id']} {endpoint['system']}/{endpoint['name']} {endpoint['service']}")
    return f'{result["state"]} "{name}" count={result["count"]}|duration_ms={result["duration_ms"]} {_safe(result["message"])}'


def report_line(endpoints: list[dict], results: list[dict]) -> str:
    ok = sum(item["state"] == 0 for item in results)
    warn = sum(item["state"] == 1 for item in results)
    crit = sum(item["state"] == 2 for item in results)
    return f"{ok} von {len(endpoints)} OK, {warn} WARN, {crit} CRIT"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DCMSim CheckMK Local Check")
    parser.add_argument("--all", action="store_true", help="auch nicht überwachte Endpoints prüfen")
    parser.add_argument("--report", action="store_true", help="lesbaren Sammelbericht ausgeben")
    parser.add_argument("--system", help="nur dieses DICOM-System prüfen")
    parser.add_argument("--service", choices=("MWL", "STORE", "QR"))
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--per-endpoint-timeout", type=float, default=25)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    configure_logging("ERROR")
    if args.worker:
        print(json.dumps(check_endpoint(json.loads(sys.stdin.read()))))
        return 0
    if args.timeout <= 0 or not 1 <= args.jobs <= 16 or args.per_endpoint_timeout <= 0:
        parser.error("Timeout muss positiv und jobs zwischen 1 und 16 sein")
    try:
        endpoints = load_endpoints(include_all=args.all, system=args.system, service=args.service)
    except Exception:
        print('2 "DCMSim Datenbank" count=0|duration_ms=0 MONITOR_DATABASE_ERROR: SQLite-Pfad und Migration prüfen.')
        return 2
    results = run_checks(endpoints, timeout=args.timeout, jobs=args.jobs, per_endpoint_timeout=args.per_endpoint_timeout)
    if args.report:
        print(report_line(endpoints, results))
        for endpoint, result in zip(endpoints, results, strict=True):
            print(f"{endpoint['system']}/{endpoint['name']} ({endpoint['service']}): {['OK', 'WARN', 'CRIT'][result['state']]} - {result['message']}")
        return 2 if any(item["state"] == 2 for item in results) else 1 if any(item["state"] == 1 for item in results) else 0
    for endpoint, result in zip(endpoints, results, strict=True):
        print(local_check_line(endpoint, result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
