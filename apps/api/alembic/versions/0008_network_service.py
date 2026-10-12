"""Add proxy user attribution and endpoint monitoring configuration."""

from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("test_runs") as batch:
        batch.add_column(sa.Column("username", sa.String(128), nullable=True))
        batch.create_index("ix_test_runs_username", ["username"])
    with op.batch_alter_table("dicom_endpoints") as batch:
        batch.add_column(sa.Column("monitored", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("monitor_calling_ae", sa.String(16), nullable=False, server_default="DCMSIM"))
        batch.add_column(sa.Column("monitor_window", sa.String(11), nullable=True))
        batch.add_column(sa.Column("monitor_min_count", sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    with op.batch_alter_table("dicom_endpoints") as batch:
        batch.drop_column("monitor_min_count")
        batch.drop_column("monitor_window")
        batch.drop_column("monitor_calling_ae")
        batch.drop_column("monitored")
    with op.batch_alter_table("test_runs") as batch:
        batch.drop_index("ix_test_runs_username")
        batch.drop_column("username")
