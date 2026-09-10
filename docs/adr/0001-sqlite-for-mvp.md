# ADR-0001: SQLite for MVP

**Status:** Accepted

**Context:** DCMSim ist ein lokales Single-Instance-Werkzeug ohne externe Infrastruktur.

**Decision:** SQLite persistiert Ziele und Historie über SQLAlchemy und Alembic unter `/data/dcmsim.db`.

**Consequences:** Einfacher Betrieb und Backup ohne Zusatzdienst; begrenzte horizontale Skalierung. Die Geschäftslogik bleibt für einen späteren PostgreSQL-Wechsel treiberunabhängig.

