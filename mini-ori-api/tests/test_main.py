import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.main import app
from app.models import AgendapuntDB, InformatieObjectDB, VergaderingDB


def _create_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_root():
    with _create_session() as session:
        app.dependency_overrides[get_session] = lambda: session
        client = TestClient(app)
        response = client.get("/")
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["message"] == "mini-ori-api"


def test_vergadering_crud():
    with _create_session() as session:
        app.dependency_overrides[get_session] = lambda: session
        client = TestClient(app)

        create_response = client.post(
            "/ori-mock/vergaderingen",
            json={
                "organisatie": {"gemeente": "gm0363", "naam": "Gemeente Amsterdam"},
                "dossiertype": "vergadering",
                "naam": "Raadsvergadering",
            },
        )
        assert create_response.status_code == 201
        vergadering = create_response.json()

        get_response = client.get(f"/ori-mock/vergaderingen/{vergadering['id']}")
        assert get_response.status_code == 200

        update_response = client.put(
            f"/ori-mock/vergaderingen/{vergadering['id']}",
            json={
                **vergadering,
                "naam": "Raadsvergadering bijgewerkt",
            },
        )
        assert update_response.status_code == 201
        assert update_response.json()["naam"] == "Raadsvergadering bijgewerkt"

        delete_response = client.delete(f"/ori-mock/vergaderingen/{vergadering['id']}")
        assert delete_response.status_code == 200

        app.dependency_overrides.clear()


def test_agendapunt_crud():
    with _create_session() as session:
        app.dependency_overrides[get_session] = lambda: session
        client = TestClient(app)

        vergadering_response = client.post(
            "/ori-mock/vergaderingen",
            json={
                "organisatie": {"gemeente": "gm0363", "naam": "Gemeente Amsterdam"},
                "dossiertype": "vergadering",
                "naam": "Raadsvergadering",
            },
        )
        vergadering = vergadering_response.json()

        create_response = client.post(
            "/ori-mock/agendapunten",
            json={
                "organisatie": {"gemeente": "gm0363", "naam": "Gemeente Amsterdam"},
                "dossiertype": "agendapunt",
                "agendapuntnaam": "Begroting",
                "vergadering": vergadering["id"],
            },
        )
        assert create_response.status_code == 201
        agendapunt = create_response.json()

        get_response = client.get(f"/ori-mock/agendapunten/{agendapunt['id']}")
        assert get_response.status_code == 200

        update_response = client.put(
            f"/ori-mock/agendapunten/{agendapunt['id']}",
            json={
                **agendapunt,
                "agendapuntnaam": "Begroting update",
            },
        )
        assert update_response.status_code == 201
        assert update_response.json()["agendapuntnaam"] == "Begroting update"

        delete_response = client.delete(f"/ori-mock/agendapunten/{agendapunt['id']}")
        assert delete_response.status_code == 200

        app.dependency_overrides.clear()


def test_informatieobject_requires_x_reason_and_crud():
    with _create_session() as session:
        app.dependency_overrides[get_session] = lambda: session
        client = TestClient(app)

        vergadering_response = client.post(
            "/ori-mock/vergaderingen",
            json={
                "organisatie": {"gemeente": "gm0363", "naam": "Gemeente Amsterdam"},
                "dossiertype": "vergadering",
                "naam": "Raadsvergadering",
            },
        )
        vergadering = vergadering_response.json()

        create_response = client.post(
            "/ori-mock/informatieobjecten",
            json={
                "vergadering": vergadering["id"],
                "organisatie": {"gemeente": "gm0363", "naam": "Gemeente Amsterdam"},
                "webpaginalink": "https://example.com/doc",
                "titel": "Agenda bijlage",
                "wooinformatiecategorie": "c_db4862c3",
                "datumingediend": "2026-06-18",
            },
        )
        assert create_response.status_code == 201
        informatieobject = create_response.json()

        missing_header_put = client.put(
            f"/ori-mock/informatieobjecten/{informatieobject['id']}",
            json={
                **informatieobject,
                "titel": "Nieuw titel",
            },
        )
        assert missing_header_put.status_code == 422

        update_response = client.put(
            f"/ori-mock/informatieobjecten/{informatieobject['id']}",
            headers={"X-Reason": "correctie"},
            json={
                **informatieobject,
                "titel": "Nieuw titel",
            },
        )
        assert update_response.status_code == 201
        assert update_response.json()["titel"] == "Nieuw titel"

        missing_header_delete = client.delete(f"/ori-mock/informatieobjecten/{informatieobject['id']}")
        assert missing_header_delete.status_code == 422

        delete_response = client.delete(
            f"/ori-mock/informatieobjecten/{informatieobject['id']}",
            headers={"X-Reason": "opschoning"},
        )
        assert delete_response.status_code == 200

        app.dependency_overrides.clear()


def test_404_on_missing_resource():
    with _create_session() as session:
        app.dependency_overrides[get_session] = lambda: session
        client = TestClient(app)

        missing_id = str(uuid.uuid4())
        response = client.get(f"/ori-mock/vergaderingen/{missing_id}")
        assert response.status_code == 404

        app.dependency_overrides.clear()
