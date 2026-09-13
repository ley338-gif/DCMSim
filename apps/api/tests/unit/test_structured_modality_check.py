from app.db.base import Base
from app.models import Area, DicomEndpoint, DicomSystem, ModalityProfile, Site, WorklistChannel
from app.services import modality_checks
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_structured_check_resolves_endpoints_and_does_not_retry_zero_results(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        site = Site(name="Nord")
        db.add(site)
        db.flush()
        area = Area(name="Radiologie", site_id=site.id)
        system = DicomSystem(name="KIS/PACS")
        db.add_all([area, system])
        db.flush()
        mwl = DicomEndpoint(system_id=system.id, name="RIS", service="MWL", host="ris.local", port=104, called_ae="RIS_MWL")
        store = DicomEndpoint(system_id=system.id, name="PACS", service="STORE", host="pacs.local", port=11112, called_ae="PACS")
        db.add_all([mwl, store])
        db.flush()
        channel = WorklistChannel(
            name="CT Worklist", area_id=area.id, modality_code="CT", mwl_endpoint_id=mwl.id,
            station_ae_mode="fixed", station_ae_fixed_value="ROOM_CT",
            modality_filter_mode="omit", modality_filter_fixed_value=None,
        )
        db.add(channel)
        db.flush()
        profile = ModalityProfile(
            name="CT 1", description=None, modality="CT", calling_ae="CT01",
            mwl_enabled=True, store_enabled=True, area_id=area.id,
            worklist_channel_id=channel.id, store_endpoint_id=store.id,
        )
        db.add(profile)
        db.commit()

        calls = []

        def find(endpoint, query):
            calls.append((endpoint, query))
            return {"success": True, "status": "0x0000", "count": 0, "entries": [], "duration_ms": 1, "steps": ["Association accepted"]}

        stored = {}

        def send(endpoint, _dataset):
            stored.update(endpoint)
            return {"success": True, "status": "0x0000", "duration_ms": 1, "steps": ["Association accepted"]}

        monkeypatch.setattr(modality_checks, "find_worklist", find)
        monkeypatch.setattr(modality_checks, "store_dataset", send)
        result = modality_checks.run_modality_check(db, profile)

        assert len(calls) == 1
        endpoint, query = calls[0]
        assert endpoint == {"host": "ris.local", "port": 104, "called_ae": "RIS_MWL", "calling_ae": "CT01", "endpoint_id": mwl.id}
        step = query.ScheduledProcedureStepSequence[0]
        assert step.ScheduledStationAETitle == "ROOM_CT"
        assert step.Modality == ""
        assert stored["host"] == "pacs.local"
        assert stored["called_ae"] == "PACS"
        assert "diagnostic_retry" not in result["worklist"]
        assert result["worklist"]["privacy"] == "No automatic broad query was sent"
