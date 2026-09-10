"""Initial target and test history schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "targets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("host", sa.String(255), nullable=False),
        sa.Column("mwl_enabled", sa.Boolean(), nullable=False),
        sa.Column("mwl_port", sa.Integer()),
        sa.Column("mwl_called_ae", sa.String(16)),
        sa.Column("store_enabled", sa.Boolean(), nullable=False),
        sa.Column("store_port", sa.Integer()),
        sa.Column("store_called_ae", sa.String(16)),
        sa.Column("default_calling_ae", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "test_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("test_type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.Integer(), sa.ForeignKey("targets.id", ondelete="SET NULL")),
        sa.Column("manual_target_json", sa.JSON()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(64), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_test_runs_started_at", "test_runs", ["started_at"])
    op.create_index("ix_test_runs_test_type", "test_runs", ["test_type"])


def downgrade():
    op.drop_table("test_runs")
    op.drop_table("targets")

