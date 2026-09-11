import pytest
from app.dicom.errors import DicomFindError, DicomPresentationContextError
from app.models import ModalityProfile, Target
from app.models import TestRun as RunModel
from app.services import modality_checks
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


@pytest.fixture
def profile_and_db():
    from app.db.base import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as database:
        target = Target(
            name="JiveX",
            host="127.0.0.1",
            mwl_enabled=True,
            mwl_port=11112,
            mwl_called_ae="JIVEXWL",
            store_enabled=True,
            store_port=11113,
            store_called_ae="JIVEX",
            default_calling_ae="DCMSIM",
        )
        database.add(target)
        database.flush()
        profile = ModalityProfile(
            name="Aplio 300",
            description=None,
            modality="US",
            calling_ae="APLIO02",
            mwl_enabled=True,
            mwl_target_id=target.id,
            store_enabled=True,
            store_target_id=target.id,
        )
        database.add(profile)
        database.commit()
        yield profile, database


def successful_find(_endpoint, _query):
    return {
        "success": True,
        "status": "0x0000",
        "count": 14,
        "entries": [{"patient_id": "NOT-PERSISTED"}],
        "duration_ms": 8,
        "steps": ["Association accepted", "C-FIND completed successfully"],
    }


def successful_store(_endpoint, _dataset):
    return {
        "success": True,
        "status": "0x0000",
        "duration_ms": 12,
        "steps": ["Association accepted", "C-STORE response received"],
    }


def test_modality_to_sop_class_mapping():
    assert modality_checks.MODALITY_SOP_CLASS == {
        "CT": "ct",
        "MR": "mr",
        "US": "ultrasound",
        "CR": "cr",
        "DX": "dx",
    }


def test_combined_modality_check_succeeds_and_persists_parent_history(
    profile_and_db, monkeypatch
):
    profile, database = profile_and_db
    monkeypatch.setattr(modality_checks, "find_worklist", successful_find)
    monkeypatch.setattr(modality_checks, "store_dataset", successful_store)

    result = modality_checks.run_modality_check(database, profile)

    assert result["overall"] == "success"
    assert result["worklist"]["count"] == 14
    assert result["store"]["status"] == "0x0000"
    assert result["store"]["sop_key"] == "ultrasound"
    run = database.scalar(
        select(RunModel).where(RunModel.id == result["run_id"])
    )
    assert run.test_type == "modality_check"
    assert run.result_json["profile_id"] == profile.id
    assert "entries" not in run.result_json["worklist"]


def test_zero_worklist_results_retry_without_station_ae(profile_and_db, monkeypatch):
    profile, database = profile_and_db
    counts = iter([0, 18])

    def find(_endpoint, query):
        count = next(counts)
        station = query.ScheduledProcedureStepSequence[0].ScheduledStationAETitle
        assert station == ("APLIO02" if count == 0 else "")
        return {
            "success": True,
            "status": "0x0000",
            "count": count,
            "entries": [],
            "duration_ms": 4,
            "steps": ["Association accepted"],
        }

    monkeypatch.setattr(modality_checks, "find_worklist", find)
    monkeypatch.setattr(modality_checks, "store_dataset", successful_store)
    result = modality_checks.run_modality_check(database, profile)
    assert result["worklist"]["count"] == 0
    assert result["worklist"]["diagnostic_retry"]["count"] == 18
    assert "without Station AE, 18 entries" in result["worklist"]["observation"]
    assert result["overall"] == "success"


@pytest.mark.parametrize("failed_service", ["worklist", "store"])
def test_partial_failure_makes_overall_result_fail(profile_and_db, monkeypatch, failed_service):
    profile, database = profile_and_db

    def failed_find(_endpoint, _query):
        raise DicomFindError("C-FIND failed", {"status": "0xA700"})

    def failed_store(_endpoint, _dataset):
        raise DicomPresentationContextError("No acceptable presentation context")

    monkeypatch.setattr(
        modality_checks,
        "find_worklist",
        failed_find if failed_service == "worklist" else successful_find,
    )
    monkeypatch.setattr(
        modality_checks,
        "store_dataset",
        failed_store if failed_service == "store" else successful_store,
    )
    result = modality_checks.run_modality_check(database, profile)
    assert result["overall"] == "failure"
    assert result[failed_service]["success"] is False
    assert result["status"] == "FAIL"


def test_missing_target_is_reported_without_network_call(profile_and_db, monkeypatch):
    profile, database = profile_and_db
    profile.mwl_target_id = None
    profile.mwl_target = None
    monkeypatch.setattr(modality_checks, "store_dataset", successful_store)
    result = modality_checks.run_modality_check(database, profile)
    assert result["worklist"]["code"] == "MODALITY_TARGET_MISSING"
    assert result["overall"] == "failure"
