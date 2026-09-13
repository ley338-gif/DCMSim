import app.models  # noqa: F401
import pytest
from app.db.base import Base
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError


def test_sqlalchemy_metadata_enforces_topology_check_constraints(tmp_path):
    database = tmp_path / "metadata-constraints.db"
    engine = create_engine(f"sqlite:///{database}")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO dicom_systems (id,name,created_at,updated_at) VALUES (1,'RIS','2026-09-12','2026-09-12')"
        )
    with engine.begin() as connection, pytest.raises(IntegrityError):
        connection.exec_driver_sql(
            "INSERT INTO dicom_endpoints (id,system_id,name,service,host,port,called_ae,created_at,updated_at) VALUES (1,1,'Bad','PRINT','ris.local',104,'RIS','2026-09-12','2026-09-12')"
        )
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO dicom_endpoints (id,system_id,name,service,host,port,called_ae,created_at,updated_at) VALUES (1,1,'MWL','MWL','ris.local',104,'RIS','2026-09-12','2026-09-12')"
        )
    with engine.begin() as connection, pytest.raises(IntegrityError):
        connection.exec_driver_sql(
            "INSERT INTO worklist_channels (id,name,area_id,modality_code,mwl_endpoint_id,station_ae_mode,station_ae_fixed_value,modality_filter_mode,modality_filter_fixed_value,created_at,updated_at) VALUES (1,'Bad',NULL,'CT',1,'fixed',NULL,'profile',NULL,'2026-09-12','2026-09-12')"
        )
