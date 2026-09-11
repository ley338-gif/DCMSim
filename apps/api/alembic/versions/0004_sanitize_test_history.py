"""Remove patient identifiers from existing test history."""

import json

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            "SELECT id, test_type, result_json FROM test_runs "
            "WHERE test_type IN ('mwl_find', 'qr_find', 'dicom_store')"
        )
    ).mappings().all()
    for row in rows:
        raw = row["result_json"]
        try:
            result = json.loads(raw) if isinstance(raw, str) else dict(raw)
        except (TypeError, ValueError):
            continue
        if row["test_type"] in {"mwl_find", "qr_find"}:
            result.pop("entries", None)
            result.pop("active_filters", None)
        if row["test_type"] == "dicom_store":
            result.pop("patient_name", None)
            result.pop("patient_id", None)
        connection.execute(
            sa.text("UPDATE test_runs SET result_json = :result WHERE id = :id"),
            {"id": row["id"], "result": json.dumps(result)},
        )


def downgrade():
    # Removed patient identifiers cannot and must not be reconstructed.
    pass
