from app.db.session import get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker


def test_readiness_checks_database(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'readiness.db'}")
    sessions = sessionmaker(bind=engine)

    def available_db():
        with sessions() as session:
            yield session

    app.dependency_overrides[get_db] = available_db
    try:
        with TestClient(app) as client:
            response = client.get("/api/ready")
            assert response.status_code == 200
            assert response.json() == {"status": "ready", "version": "0.3.16"}
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_readiness_fails_without_database_but_liveness_stays_ok():
    class UnavailableDatabase:
        def execute(self, _statement):
            raise OperationalError("SELECT 1", {}, Exception("connection failed"))

    app.dependency_overrides[get_db] = lambda: UnavailableDatabase()
    try:
        with TestClient(app) as client:
            assert client.get("/api/health").json()["status"] == "ok"
            response = client.get("/api/ready")
            assert response.status_code == 503
            assert response.json() == {"detail": "Database unavailable"}
    finally:
        app.dependency_overrides.clear()
