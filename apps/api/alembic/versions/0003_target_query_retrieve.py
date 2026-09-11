"""Add Query/Retrieve endpoint configuration to targets."""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "targets",
        sa.Column("qr_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("targets", sa.Column("qr_port", sa.Integer(), nullable=True))
    op.add_column("targets", sa.Column("qr_called_ae", sa.String(16), nullable=True))


def downgrade():
    op.drop_column("targets", "qr_called_ae")
    op.drop_column("targets", "qr_port")
    op.drop_column("targets", "qr_enabled")
