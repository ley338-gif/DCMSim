"""Add modality profiles referencing existing targets."""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "modality_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.String(500)),
        sa.Column("modality", sa.String(8), nullable=False),
        sa.Column("calling_ae", sa.String(16), nullable=False),
        sa.Column("mwl_enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "mwl_target_id",
            sa.Integer(),
            sa.ForeignKey("targets.id", ondelete="SET NULL"),
        ),
        sa.Column("store_enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "store_target_id",
            sa.Integer(),
            sa.ForeignKey("targets.id", ondelete="SET NULL"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_modality_profiles_mwl_target_id", "modality_profiles", ["mwl_target_id"])
    op.create_index(
        "ix_modality_profiles_store_target_id", "modality_profiles", ["store_target_id"]
    )


def downgrade():
    op.drop_index("ix_modality_profiles_store_target_id", table_name="modality_profiles")
    op.drop_index("ix_modality_profiles_mwl_target_id", table_name="modality_profiles")
    op.drop_table("modality_profiles")
