"""Add explicit ownership marker for internal worklist channels."""

from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("worklist_channels") as batch:
        batch.add_column(
            sa.Column(
                "is_internal",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade():
    with op.batch_alter_table("worklist_channels") as batch:
        batch.drop_column("is_internal")
