"""Normalize organizational and DICOM topology while preserving legacy history."""

from hashlib import sha256

from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def _suffixed_node_name(base: str, suffix: str) -> str:
    candidate = f"{base} – {suffix}"
    if len(candidate) <= 120:
        return candidate
    digest = sha256(base.encode("utf-8")).hexdigest()[:8]
    ending = f" – {digest} – {suffix}"
    return f"{base[: 120 - len(ending)]}{ending}"


def upgrade():
    op.create_table(
        "sites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "areas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("site_id", "name", name="uq_area_site_name"),
    )
    op.create_index("ix_areas_site_id", "areas", ["site_id"])
    op.create_table(
        "dicom_systems",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "dicom_endpoints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("system_id", sa.Integer(), sa.ForeignKey("dicom_systems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("service", sa.String(8), nullable=False),
        sa.Column("host", sa.String(255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("called_ae", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("system_id", "name", name="uq_endpoint_system_name"),
        sa.CheckConstraint("service IN ('MWL', 'STORE', 'QR')", name="ck_endpoint_service"),
    )
    op.create_index("ix_dicom_endpoints_system_id", "dicom_endpoints", ["system_id"])
    op.create_index("ix_dicom_endpoints_service", "dicom_endpoints", ["service"])
    op.create_table(
        "worklist_channels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("area_id", sa.Integer(), sa.ForeignKey("areas.id", ondelete="SET NULL"), nullable=True),
        sa.Column("modality_code", sa.String(8), nullable=False),
        sa.Column("mwl_endpoint_id", sa.Integer(), sa.ForeignKey("dicom_endpoints.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("station_ae_mode", sa.String(8), nullable=False),
        sa.Column("station_ae_fixed_value", sa.String(16), nullable=True),
        sa.Column("modality_filter_mode", sa.String(8), nullable=False),
        sa.Column("modality_filter_fixed_value", sa.String(16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "station_ae_mode IN ('profile', 'fixed', 'omit')",
            name="ck_channel_station_ae_mode",
        ),
        sa.CheckConstraint(
            "(station_ae_mode = 'fixed' AND station_ae_fixed_value IS NOT NULL AND "
            "length(trim(station_ae_fixed_value)) BETWEEN 1 AND 16) OR "
            "(station_ae_mode IN ('profile', 'omit') AND station_ae_fixed_value IS NULL)",
            name="ck_channel_station_ae_fixed_value",
        ),
        sa.CheckConstraint(
            "modality_filter_mode IN ('profile', 'fixed', 'omit')",
            name="ck_channel_modality_filter_mode",
        ),
        sa.CheckConstraint(
            "(modality_filter_mode = 'fixed' AND modality_filter_fixed_value IS NOT NULL AND "
            "modality_filter_fixed_value IN "
            "('CT','MR','US','CR','DX','OT','XA','MG','NM','PT')) OR "
            "(modality_filter_mode IN ('profile', 'omit') AND modality_filter_fixed_value IS NULL)",
            name="ck_channel_modality_filter_fixed_value",
        ),
    )
    op.create_index("ix_worklist_channels_area_id", "worklist_channels", ["area_id"])
    op.create_index("ix_worklist_channels_mwl_endpoint_id", "worklist_channels", ["mwl_endpoint_id"])
    with op.batch_alter_table("modality_profiles") as batch:
        batch.add_column(sa.Column("area_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("worklist_channel_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("store_endpoint_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_profile_area", "areas", ["area_id"], ["id"], ondelete="SET NULL")
        batch.create_foreign_key("fk_profile_channel", "worklist_channels", ["worklist_channel_id"], ["id"], ondelete="SET NULL")
        batch.create_foreign_key("fk_profile_store_endpoint", "dicom_endpoints", ["store_endpoint_id"], ["id"], ondelete="SET NULL")
        batch.create_index("ix_modality_profiles_area_id", ["area_id"])
        batch.create_index("ix_modality_profiles_worklist_channel_id", ["worklist_channel_id"])
        batch.create_index("ix_modality_profiles_store_endpoint_id", ["store_endpoint_id"])

    connection = op.get_bind()
    targets = connection.execute(sa.text("SELECT * FROM targets ORDER BY id")).mappings().all()
    endpoint_ids = {}
    for target in targets:
        connection.execute(
            sa.text("INSERT INTO dicom_systems (id,name,created_at,updated_at) VALUES (:id,:name,:created_at,:updated_at)"),
            dict(target),
        )
        for service, enabled, port, called_ae in (
            ("MWL", target["mwl_enabled"], target["mwl_port"], target["mwl_called_ae"]),
            ("STORE", target["store_enabled"], target["store_port"], target["store_called_ae"]),
            ("QR", target["qr_enabled"], target["qr_port"], target["qr_called_ae"]),
        ):
            if not enabled or not port or not called_ae:
                continue
            result = connection.execute(
                sa.text(
                    "INSERT INTO dicom_endpoints (system_id,name,service,host,port,called_ae,created_at,updated_at) "
                    "VALUES (:system_id,:name,:service,:host,:port,:called_ae,:created_at,:updated_at)"
                ),
                {
                    "system_id": target["id"], "name": _suffixed_node_name(target["name"], service),
                    "service": service, "host": target["host"], "port": port,
                    "called_ae": called_ae, "created_at": target["created_at"], "updated_at": target["updated_at"],
                },
            )
            endpoint_ids[(target["id"], service)] = result.lastrowid

    profiles = connection.execute(sa.text("SELECT * FROM modality_profiles ORDER BY id")).mappings().all()
    for profile in profiles:
        channel_id = None
        mwl_endpoint_id = endpoint_ids.get((profile["mwl_target_id"], "MWL"))
        if profile["mwl_enabled"] and mwl_endpoint_id:
            result = connection.execute(
                sa.text(
                    "INSERT INTO worklist_channels (name,area_id,modality_code,mwl_endpoint_id,station_ae_mode,station_ae_fixed_value,modality_filter_mode,modality_filter_fixed_value,created_at,updated_at) "
                    "VALUES (:name,NULL,:modality,:endpoint,'profile',NULL,'profile',NULL,:created_at,:updated_at)"
                ),
                {"name": _suffixed_node_name(profile["name"], "Worklist"), "modality": profile["modality"], "endpoint": mwl_endpoint_id, "created_at": profile["created_at"], "updated_at": profile["updated_at"]},
            )
            channel_id = result.lastrowid
        store_endpoint_id = endpoint_ids.get((profile["store_target_id"], "STORE")) if profile["store_enabled"] else None
        connection.execute(
            sa.text(
                "UPDATE modality_profiles SET area_id=NULL, worklist_channel_id=:channel, "
                "store_endpoint_id=:store, "
                "mwl_target_id=CASE WHEN :channel IS NOT NULL THEN NULL ELSE mwl_target_id END, "
                "store_target_id=CASE WHEN :store IS NOT NULL THEN NULL ELSE store_target_id END "
                "WHERE id=:id"
            ),
            {"channel": channel_id, "store": store_endpoint_id, "id": profile["id"]},
        )


def downgrade():
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE modality_profiles SET "
            "mwl_target_id=COALESCE(mwl_target_id, (SELECT t.id FROM worklist_channels wc "
            "JOIN dicom_endpoints de ON de.id=wc.mwl_endpoint_id "
            "JOIN dicom_systems ds ON ds.id=de.system_id JOIN targets t ON "
            "(t.id=ds.id OR (t.name=ds.name AND NOT EXISTS "
            "(SELECT 1 FROM targets stable_target WHERE stable_target.id=ds.id))) "
            "WHERE wc.id=modality_profiles.worklist_channel_id)), "
            "store_target_id=COALESCE(store_target_id, (SELECT t.id FROM dicom_endpoints de "
            "JOIN dicom_systems ds ON ds.id=de.system_id JOIN targets t ON "
            "(t.id=ds.id OR (t.name=ds.name AND NOT EXISTS "
            "(SELECT 1 FROM targets stable_target WHERE stable_target.id=ds.id))) "
            "WHERE de.id=modality_profiles.store_endpoint_id))"
        )
    )
    with op.batch_alter_table("modality_profiles") as batch:
        batch.drop_index("ix_modality_profiles_store_endpoint_id")
        batch.drop_index("ix_modality_profiles_worklist_channel_id")
        batch.drop_index("ix_modality_profiles_area_id")
        batch.drop_constraint("fk_profile_store_endpoint", type_="foreignkey")
        batch.drop_constraint("fk_profile_channel", type_="foreignkey")
        batch.drop_constraint("fk_profile_area", type_="foreignkey")
        batch.drop_column("store_endpoint_id")
        batch.drop_column("worklist_channel_id")
        batch.drop_column("area_id")
    op.drop_table("worklist_channels")
    op.drop_table("dicom_endpoints")
    op.drop_table("dicom_systems")
    op.drop_table("areas")
    op.drop_table("sites")
