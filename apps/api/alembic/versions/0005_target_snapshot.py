"""Preserve the technical endpoint used by each test run."""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("test_runs", sa.Column("target_snapshot_json", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("test_runs", "target_snapshot_json")
