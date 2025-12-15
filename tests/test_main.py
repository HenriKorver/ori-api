import pytest
import uuid
import datetime
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models import VergaderingDB, AgendapuntDB, InformatieObjectDB


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory test database"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with overridden database session"""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# Test root endpoint
def test_root_endpoint(client: TestClient):
    """Test that root endpoint returns expected response"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["version"] == "0.1.0"


# Vergadering tests
def test_create_vergadering(client: TestClient):
    """Test creating a new vergadering"""
    response = client.post(
        "/vergaderingen",
        json={
            "organisatie": {"gemeente": "gm0363", "naam": "Gemeente Amsterdam"},
            "dossiertype": "vergadering",
            "naam": "Raadsvergadering",
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["naam"] == "Raadsvergadering"
    assert data["dossiertype"] == "vergadering"
    assert data["pid"] is not None
    # PID should be a UUID
    uuid.UUID(data["pid"])  # Will raise if not valid UUID


def test_get_vergaderingen(session: Session, client: TestClient):
    """Test retrieving all vergaderingen"""
    # Create test data
    vergadering1 = VergaderingDB(
        pid=str(uuid.uuid4()),
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="vergadering",
        naam="Raadsvergadering"
    )
    vergadering2 = VergaderingDB(
        pid=str(uuid.uuid4()),
        organisatie_type="provincie",
        organisatie_code="pv27",
        organisatie_naam="Provincie Groningen",
        dossiertype="vergadering",
        naam="Provinciale Vergadering"
    )
    session.add(vergadering1)
    session.add(vergadering2)
    session.commit()

    # Test the API
    response = client.get("/vergaderingen")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    assert data["results"][0]["naam"] == "Raadsvergadering"
    assert data["results"][1]["naam"] == "Provinciale Vergadering"


def test_get_vergadering(session: Session, client: TestClient):
    """Test retrieving a specific vergadering"""
    test_pid = str(uuid.uuid4())
    vergadering = VergaderingDB(
        pid=test_pid,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="vergadering",
        naam="Raadsvergadering"
    )
    session.add(vergadering)
    session.commit()

    response = client.get(f"/vergaderingen/{vergadering.pid}")
    assert response.status_code == 200
    data = response.json()
    assert data["naam"] == "Raadsvergadering"
    assert data["pid"] == test_pid


def test_update_vergadering(session: Session, client: TestClient):
    """Test updating a vergadering"""
    test_pid = str(uuid.uuid4())
    vergadering = VergaderingDB(
        pid=test_pid,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="vergadering",
        naam="Oude Naam"
    )
    session.add(vergadering)
    session.commit()

    response = client.put(
        f"/vergaderingen/{vergadering.pid}",
        json={
            "organisatie": {"gemeente": "gm0363", "naam": "Gemeente Amsterdam"},
            "dossiertype": "vergadering",
            "naam": "Nieuwe Naam",
            "pid": vergadering.pid,
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["naam"] == "Nieuwe Naam"


def test_delete_vergadering(session: Session, client: TestClient):
    """Test deleting a vergadering"""
    test_pid = str(uuid.uuid4())
    vergadering = VergaderingDB(
        pid=test_pid,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="vergadering",
        naam="Te Verwijderen Vergadering"
    )
    session.add(vergadering)
    session.commit()

    response = client.delete(f"/vergaderingen/{vergadering.pid}")
    assert response.status_code == 200

    vergadering_in_db = session.get(VergaderingDB, vergadering.id)
    assert vergadering_in_db is None


# Agendapunt tests
def test_create_agendapunt(client: TestClient):
    """Test creating a new agendapunt"""
    response = client.post(
        "/agendapunten",
        json={
            "organisatie": {"gemeente": "gm0363", "naam": "Gemeente Amsterdam"},
            "dossiertype": "agendapunt",
            "agendapuntnaam": "Begrotingsbespreking",
            "vergadering": {"id": "1", "url": "http://localhost:8000/vergaderingen/1"},
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["agendapuntnaam"] == "Begrotingsbespreking"
    assert data["dossiertype"] == "agendapunt"
    assert data["pid"] is not None
    # PID should be a UUID
    uuid.UUID(data["pid"])  # Will raise if not valid UUID


def test_get_agendapunten(session: Session, client: TestClient):
    """Test retrieving all agendapunten"""
    agendapunt1 = AgendapuntDB(
        pid=str(uuid.uuid4()),
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="agendapunt",
        agendapuntnaam="Agendapunt 1",
        vergadering_id=None,
    )
    agendapunt2 = AgendapuntDB(
        pid=str(uuid.uuid4()),
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="agendapunt",
        agendapuntnaam="Agendapunt 2",
        vergadering_id=None,
    )
    session.add(agendapunt1)
    session.add(agendapunt2)
    session.commit()

    response = client.get("/agendapunten")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2


# Informatieobject tests
def test_create_informatieobject(client: TestClient):
    """Test creating a new informatieobject"""
    response = client.post(
        "/informatieobjecten",
        json={
            "organisatie": {"gemeente": "gm0363", "naam": "Gemeente Amsterdam"},
            "webpaginalink": "https://example.com/document",
            "titel": "Testdocument",
            "wooinformatiecategorie": "c_db4862c3",
            "datumingediend": "2025-12-15",
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["titel"] == "Testdocument"
    assert data["pid"] is not None
    # PID should be a UUID
    uuid.UUID(data["pid"])  # Will raise if not valid UUID


def test_get_informatieobjecten(session: Session, client: TestClient):
    """Test retrieving all informatieobjecten"""
    obj1 = InformatieObjectDB(
        pid=str(uuid.uuid4()),
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        webpaginalink="https://example.com/doc1",
        titel="Document 1",
        wooinformatiecategorie="c_db4862c3",
        datumingediend=datetime.date.today(),
    )
    obj2 = InformatieObjectDB(
        pid=str(uuid.uuid4()),
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        webpaginalink="https://example.com/doc2",
        titel="Document 2",
        wooinformatiecategorie="c_db4862c3",
        datumingediend=datetime.date.today(),
    )
    session.add(obj1)
    session.add(obj2)
    session.commit()

    response = client.get("/informatieobjecten")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2


# Error handling tests
def test_get_nonexistent_vergadering(client: TestClient):
    """Test that getting a non-existent vergadering returns 404"""
    nonexistent_uuid = str(uuid.uuid4())
    response = client.get(f"/vergaderingen/{nonexistent_uuid}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_create_vergadering_missing_required_field(client: TestClient):
    """Test that creating vergadering without required fields returns 422"""
    response = client.post(
        "/vergaderingen",
        json={
            "organisatie": {"gemeente": "gm0363", "naam": "Gemeente Amsterdam"},
            # missing dossiertype and naam
        }
    )
    assert response.status_code == 422


def test_create_agendapunt_missing_required_field(client: TestClient):
    """Test that creating agendapunt without required fields returns 422"""
    response = client.post(
        "/agendapunten",
        json={
            "organisatie": {"gemeente": "gm0363", "naam": "Gemeente Amsterdam"},
            # missing dossiertype, agendapuntnaam, and vergadering
        }
    )
    assert response.status_code == 422
