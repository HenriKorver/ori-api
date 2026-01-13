import pytest
import uuid
import datetime
from datetime import date
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
    assert data["pid_uuid"] is not None
    # PID should be a URL
    assert data["pid"].startswith("http://localhost:8000/vergaderingen/")
    # PID_UUID should be a valid UUID
    uuid.UUID(data["pid_uuid"])


def test_get_vergaderingen(session: Session, client: TestClient):
    """Test retrieving all vergaderingen"""
    # Create test data
    uuid1 = str(uuid.uuid4())
    uuid2 = str(uuid.uuid4())
    vergadering1 = VergaderingDB(
        pid=f"http://localhost:8000/vergaderingen/{uuid1}",
        pid_uuid=uuid1,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="vergadering",
        naam="Raadsvergadering"
    )
    vergadering2 = VergaderingDB(
        pid=f"http://localhost:8000/vergaderingen/{uuid2}",
        pid_uuid=uuid2,
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
    test_uuid = str(uuid.uuid4())
    test_pid = f"http://localhost:8000/vergaderingen/{test_uuid}"
    vergadering = VergaderingDB(
        pid=test_pid,
        pid_uuid=test_uuid,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="vergadering",
        naam="Raadsvergadering"
    )
    session.add(vergadering)
    session.commit()

    response = client.get(f"/vergaderingen/{vergadering.pid_uuid}")
    assert response.status_code == 200
    data = response.json()
    assert data["naam"] == "Raadsvergadering"
    assert data["pid"] == test_pid
    assert data["pid_uuid"] == test_uuid


def test_update_vergadering(session: Session, client: TestClient):
    """Test updating a vergadering"""
    test_uuid = str(uuid.uuid4())
    test_pid = f"http://localhost:8000/vergaderingen/{test_uuid}"
    vergadering = VergaderingDB(
        pid=test_pid,
        pid_uuid=test_uuid,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="vergadering",
        naam="Oude Naam"
    )
    session.add(vergadering)
    session.commit()

    response = client.put(
        f"/vergaderingen/{vergadering.pid_uuid}",
        json={
            "organisatie": {"gemeente": "gm0363", "naam": "Gemeente Amsterdam"},
            "dossiertype": "vergadering",
            "naam": "Nieuwe Naam",
            "pid": vergadering.pid,
            "pid_uuid": vergadering.pid_uuid,
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["naam"] == "Nieuwe Naam"


def test_delete_vergadering(session: Session, client: TestClient):
    """Test deleting a vergadering"""
    test_uuid = str(uuid.uuid4())
    test_pid = f"http://localhost:8000/vergaderingen/{test_uuid}"
    vergadering = VergaderingDB(
        pid=test_pid,
        pid_uuid=test_uuid,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="vergadering",
        naam="Te Verwijderen Vergadering"
    )
    session.add(vergadering)
    session.commit()

    response = client.delete(f"/vergaderingen/{vergadering.pid_uuid}")
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
    assert data["pid_uuid"] is not None
    # PID should be a URL
    assert data["pid"].startswith("http://localhost:8000/agendapunten/")
    # PID_UUID should be a valid UUID
    uuid.UUID(data["pid_uuid"])


def test_get_agendapunten(session: Session, client: TestClient):
    """Test retrieving all agendapunten"""
    uuid1 = str(uuid.uuid4())
    uuid2 = str(uuid.uuid4())
    agendapunt1 = AgendapuntDB(
        pid=f"http://localhost:8000/agendapunten/{uuid1}",
        pid_uuid=uuid1,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="agendapunt",
        agendapuntnaam="Agendapunt 1",
        vergadering_id=None,
    )
    agendapunt2 = AgendapuntDB(
        pid=f"http://localhost:8000/agendapunten/{uuid2}",
        pid_uuid=uuid2,
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
    assert data["pid_uuid"] is not None
    # PID should be a URL
    assert data["pid"].startswith("http://localhost:8000/informatieobjecten/")
    # PID_UUID should be a valid UUID
    uuid.UUID(data["pid_uuid"])


def test_get_informatieobjecten(session: Session, client: TestClient):
    """Test retrieving all informatieobjecten"""
    uuid1 = str(uuid.uuid4())
    uuid2 = str(uuid.uuid4())
    obj1 = InformatieObjectDB(
        pid=f"http://localhost:8000/informatieobjecten/{uuid1}",
        pid_uuid=uuid1,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        webpaginalink="https://example.com/doc1",
        titel="Document 1",
        wooinformatiecategorie="c_db4862c3",
        datumingediend=datetime.date.today(),
    )
    obj2 = InformatieObjectDB(
        pid=f"http://localhost:8000/informatieobjecten/{uuid2}",
        pid_uuid=uuid2,
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


def test_vergadering_includes_agendapunten_references(session: Session, client: TestClient):
    """Test that a vergadering response includes references to its agendapunten."""
    # Create vergadering directly in database
    vergadering_uuid = str(uuid.uuid4())
    vergadering = VergaderingDB(
        pid=f"http://localhost:8000/vergaderingen/{vergadering_uuid}",
        pid_uuid=vergadering_uuid,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="vergadering",
        naam="Raadsvergadering",
    )
    session.add(vergadering)
    session.commit()
    session.refresh(vergadering)
    
    # Create 2 agendapunten linked to this vergadering
    uuid1 = str(uuid.uuid4())
    uuid2 = str(uuid.uuid4())
    agendapunt1 = AgendapuntDB(
        pid=f"http://localhost:8000/agendapunten/{uuid1}",
        pid_uuid=uuid1,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="agendapunt",
        agendapuntnaam="Agendapunt 1",
        vergadering_id=vergadering.id,
    )
    agendapunt2 = AgendapuntDB(
        pid=f"http://localhost:8000/agendapunten/{uuid2}",
        pid_uuid=uuid2,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="agendapunt",
        agendapuntnaam="Agendapunt 2",
        vergadering_id=vergadering.id,
    )
    session.add(agendapunt1)
    session.add(agendapunt2)
    session.commit()
    
    # Get vergadering and verify agendapunten field
    response = client.get(f"/vergaderingen/{vergadering.pid_uuid}")
    assert response.status_code == 200
    data = response.json()
    
    assert "agendapunten" in data
    assert len(data["agendapunten"]) == 2
    
    # Verify format of URIs
    api_server = "http://localhost:8000"
    agendapunt_uuids = [uuid1, uuid2]
    for uri in data["agendapunten"]:
        assert uri.startswith(f"{api_server}/agendapunten/")
        # Extract UUID and verify it's in our list
        uri_uuid = uri.split("/")[-1]
        assert uri_uuid in agendapunt_uuids
        # Verify it's a valid UUID format
        uuid.UUID(uri_uuid)


def test_vergadering_includes_informatieobjecten_via_agendapunten(session: Session, client: TestClient):
    """Test that a vergadering response includes informatieobjecten that are linked to its agendapunten."""
    # Create vergadering
    vergadering_uuid = str(uuid.uuid4())
    vergadering = VergaderingDB(
        pid=f"http://localhost:8000/vergaderingen/{vergadering_uuid}",
        pid_uuid=vergadering_uuid,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="vergadering",
        naam="Raadsvergadering",
    )
    session.add(vergadering)
    session.commit()
    session.refresh(vergadering)
    
    # Create 2 agendapunten linked to this vergadering
    agp_uuid1 = str(uuid.uuid4())
    agp_uuid2 = str(uuid.uuid4())
    agendapunt1 = AgendapuntDB(
        pid=f"http://localhost:8000/agendapunten/{agp_uuid1}",
        pid_uuid=agp_uuid1,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="agendapunt",
        agendapuntnaam="Agendapunt 1",
        vergadering_id=vergadering.id,
    )
    agendapunt2 = AgendapuntDB(
        pid=f"http://localhost:8000/agendapunten/{agp_uuid2}",
        pid_uuid=agp_uuid2,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="agendapunt",
        agendapuntnaam="Agendapunt 2",
        vergadering_id=vergadering.id,
    )
    session.add(agendapunt1)
    session.add(agendapunt2)
    session.commit()
    session.refresh(agendapunt1)
    session.refresh(agendapunt2)
    
    # Create 3 informatieobjecten
    info_uuid1 = str(uuid.uuid4())
    info_uuid2 = str(uuid.uuid4())
    info_uuid3 = str(uuid.uuid4())
    informatieobject1 = InformatieObjectDB(
        pid=f"http://localhost:8000/informatieobjecten/{info_uuid1}",
        pid_uuid=info_uuid1,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        titel="Document 1",
        wooinformatiecategorie="c_db4862c3",
        datumingediend=date(2017, 2, 9),
        webpaginalink="https://example.com/doc1",
    )
    informatieobject2 = InformatieObjectDB(
        pid=f"http://localhost:8000/informatieobjecten/{info_uuid2}",
        pid_uuid=info_uuid2,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        titel="Document 2",
        wooinformatiecategorie="c_db4862c3",
        datumingediend=date(2017, 2, 9),
        webpaginalink="https://example.com/doc2",
    )
    informatieobject3 = InformatieObjectDB(
        pid=f"http://localhost:8000/informatieobjecten/{info_uuid3}",
        pid_uuid=info_uuid3,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        titel="Document 3",
        wooinformatiecategorie="c_db4862c3",
        datumingediend=date(2017, 2, 9),
        webpaginalink="https://example.com/doc3",
    )
    session.add(informatieobject1)
    session.add(informatieobject2)
    session.add(informatieobject3)
    session.commit()
    session.refresh(informatieobject1)
    session.refresh(informatieobject2)
    session.refresh(informatieobject3)
    
    # Link informatieobjecten to agendapunten via junction table
    # agendapunt1 linked to info1 and info2
    # agendapunt2 linked to info2 and info3
    # Expected result: vergadering should show all three informatieobjecten
    from app.models import AgendapuntInformatieObjectLink
    
    link1 = AgendapuntInformatieObjectLink(
        agendapunt_id=agendapunt1.id,
        informatieobject_id=informatieobject1.id
    )
    link2 = AgendapuntInformatieObjectLink(
        agendapunt_id=agendapunt1.id,
        informatieobject_id=informatieobject2.id
    )
    link3 = AgendapuntInformatieObjectLink(
        agendapunt_id=agendapunt2.id,
        informatieobject_id=informatieobject2.id
    )
    link4 = AgendapuntInformatieObjectLink(
        agendapunt_id=agendapunt2.id,
        informatieobject_id=informatieobject3.id
    )
    session.add(link1)
    session.add(link2)
    session.add(link3)
    session.add(link4)
    session.commit()
    
    # Get vergadering and verify informatieobjecten field
    response = client.get(f"/vergaderingen/{vergadering.pid_uuid}")
    assert response.status_code == 200
    data = response.json()
    
    # Verify informatieobjecten field exists and has all 3 unique objects
    assert "informatieobjecten" in data
    assert len(data["informatieobjecten"]) == 3
    
    # Verify format of URIs and that all informatieobjecten are present
    api_server = "http://localhost:8000"
    expected_uuids = {info_uuid1, info_uuid2, info_uuid3}
    found_uuids = set()
    
    for uri in data["informatieobjecten"]:
        assert uri.startswith(f"{api_server}/informatieobjecten/")
        # Extract UUID
        uri_uuid = uri.split("/")[-1]
        found_uuids.add(uri_uuid)
        # Verify it's a valid UUID format
        uuid.UUID(uri_uuid)
    
    # Verify all expected UUIDs are found (no duplicates because it's a set)
    assert found_uuids == expected_uuids


def test_informatieobject_includes_vergaderingen_via_agendapunten(session: Session, client: TestClient):
    """Test that an informatieobject response includes vergaderingen via its agendapunten."""
    # Create 2 vergaderingen
    verg_uuid1 = str(uuid.uuid4())
    verg_uuid2 = str(uuid.uuid4())
    vergadering1 = VergaderingDB(
        pid=f"http://localhost:8000/vergaderingen/{verg_uuid1}",
        pid_uuid=verg_uuid1,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="vergadering",
        naam="Raadsvergadering 1",
    )
    vergadering2 = VergaderingDB(
        pid=f"http://localhost:8000/vergaderingen/{verg_uuid2}",
        pid_uuid=verg_uuid2,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="vergadering",
        naam="Raadsvergadering 2",
    )
    session.add(vergadering1)
    session.add(vergadering2)
    session.commit()
    session.refresh(vergadering1)
    session.refresh(vergadering2)
    
    # Create 3 agendapunten - 2 for vergadering1, 1 for vergadering2
    agp_uuid1 = str(uuid.uuid4())
    agp_uuid2 = str(uuid.uuid4())
    agp_uuid3 = str(uuid.uuid4())
    agendapunt1 = AgendapuntDB(
        pid=f"http://localhost:8000/agendapunten/{agp_uuid1}",
        pid_uuid=agp_uuid1,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="agendapunt",
        agendapuntnaam="Agendapunt 1",
        vergadering_id=vergadering1.id,
    )
    agendapunt2 = AgendapuntDB(
        pid=f"http://localhost:8000/agendapunten/{agp_uuid2}",
        pid_uuid=agp_uuid2,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="agendapunt",
        agendapuntnaam="Agendapunt 2",
        vergadering_id=vergadering1.id,
    )
    agendapunt3 = AgendapuntDB(
        pid=f"http://localhost:8000/agendapunten/{agp_uuid3}",
        pid_uuid=agp_uuid3,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="agendapunt",
        agendapuntnaam="Agendapunt 3",
        vergadering_id=vergadering2.id,
    )
    session.add(agendapunt1)
    session.add(agendapunt2)
    session.add(agendapunt3)
    session.commit()
    session.refresh(agendapunt1)
    session.refresh(agendapunt2)
    session.refresh(agendapunt3)
    
    # Create informatieobject
    info_uuid = str(uuid.uuid4())
    informatieobject = InformatieObjectDB(
        pid=f"http://localhost:8000/informatieobjecten/{info_uuid}",
        pid_uuid=info_uuid,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        titel="Document 1",
        wooinformatiecategorie="c_db4862c3",
        datumingediend=date(2017, 2, 9),
        webpaginalink="https://example.com/doc1",
    )
    session.add(informatieobject)
    session.commit()
    session.refresh(informatieobject)
    
    # Link informatieobject to all 3 agendapunten (2 from vergadering1, 1 from vergadering2)
    from app.models import AgendapuntInformatieObjectLink
    
    link1 = AgendapuntInformatieObjectLink(
        agendapunt_id=agendapunt1.id,
        informatieobject_id=informatieobject.id
    )
    link2 = AgendapuntInformatieObjectLink(
        agendapunt_id=agendapunt2.id,
        informatieobject_id=informatieobject.id
    )
    link3 = AgendapuntInformatieObjectLink(
        agendapunt_id=agendapunt3.id,
        informatieobject_id=informatieobject.id
    )
    session.add(link1)
    session.add(link2)
    session.add(link3)
    session.commit()
    
    # Get informatieobject and verify vergaderingen field
    response = client.get(f"/informatieobjecten/{informatieobject.pid_uuid}")
    assert response.status_code == 200
    data = response.json()
    
    # Verify vergaderingen field exists and has both vergaderingen
    assert "vergaderingen" in data
    assert data["vergaderingen"] is not None
    assert len(data["vergaderingen"]) == 2
    
    # Verify format of references and that both vergaderingen are present
    api_server = "http://localhost:8000"
    expected_uuids = {verg_uuid1, verg_uuid2}
    found_uuids = set()
    
    for ref in data["vergaderingen"]:
        assert "id" in ref
        assert ref["id"].startswith(f"{api_server}/vergaderingen/")
        # Extract UUID
        ref_uuid = ref["id"].split("/")[-1]
        found_uuids.add(ref_uuid)
        # Verify it's a valid UUID format
        uuid.UUID(ref_uuid)
    
    # Verify both expected vergaderingen are found
    assert found_uuids == expected_uuids
    
    # Also verify agendapunten are present
    assert "agendapunten" in data
    assert data["agendapunten"] is not None
    assert len(data["agendapunten"]) == 3


def test_post_informatieobject_with_vergadering_reference(session: Session, client: TestClient):
    """Test that posting an informatieobject with vergadering reference links to vergadering's agendapunten."""
    # Create vergadering
    verg_uuid = str(uuid.uuid4())
    vergadering = VergaderingDB(
        pid=f"http://localhost:8000/vergaderingen/{verg_uuid}",
        pid_uuid=verg_uuid,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="vergadering",
        naam="Raadsvergadering",
    )
    session.add(vergadering)
    session.commit()
    session.refresh(vergadering)
    
    # Create 2 agendapunten for this vergadering
    agp_uuid1 = str(uuid.uuid4())
    agp_uuid2 = str(uuid.uuid4())
    agendapunt1 = AgendapuntDB(
        pid=f"http://localhost:8000/agendapunten/{agp_uuid1}",
        pid_uuid=agp_uuid1,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="agendapunt",
        agendapuntnaam="Agendapunt 1",
        vergadering_id=vergadering.id,
    )
    agendapunt2 = AgendapuntDB(
        pid=f"http://localhost:8000/agendapunten/{agp_uuid2}",
        pid_uuid=agp_uuid2,
        organisatie_type="gemeente",
        organisatie_code="gm0363",
        organisatie_naam="Gemeente Amsterdam",
        dossiertype="agendapunt",
        agendapuntnaam="Agendapunt 2",
        vergadering_id=vergadering.id,
    )
    session.add(agendapunt1)
    session.add(agendapunt2)
    session.commit()
    
    # POST informatieobject with vergadering reference
    info_data = {
        "webpaginalink": "https://example.com/doc.pdf",
        "organisatie": {
            "gemeente": "gm0363",
            "naam": "Gemeente Amsterdam"
        },
        "titel": "Test Document",
        "wooinformatiecategorie": "c_db4862c3",
        "datumingediend": "2017-02-09",
        "vergaderingen": [{"id": f"http://localhost:8000/vergaderingen/{verg_uuid}"}]
    }
    
    response = client.post("/informatieobjecten", json=info_data)
    assert response.status_code == 201
    data = response.json()
    
    # Verify vergaderingen in response
    assert "vergaderingen" in data
    assert data["vergaderingen"] is not None
    assert len(data["vergaderingen"]) == 1
    assert data["vergaderingen"][0]["id"] == f"http://localhost:8000/vergaderingen/{verg_uuid}"
    
    # Verify it's linked to both agendapunten
    assert "agendapunten" in data
    assert data["agendapunten"] is not None
    assert len(data["agendapunten"]) == 2
    
    # Extract agendapunt UUIDs from response
    agendapunt_uuids = {ref["id"].split("/")[-1] for ref in data["agendapunten"]}
    expected_uuids = {agp_uuid1, agp_uuid2}
    assert agendapunt_uuids == expected_uuids


def test_get_vergadering_shows_linked_informatieobjecten(session: Session, client: TestClient):
    """Test that getting a vergadering shows informatieobjecten linked via agendapunten."""
    # Create vergadering via API
    verg_data = {
        "organisatie": {
            "gemeente": "gm0363",
            "naam": "Gemeente Amsterdam"
        },
        "dossiertype": "vergadering",
        "naam": "Raadsvergadering"
    }
    verg_response = client.post("/vergaderingen", json=verg_data)
    assert verg_response.status_code == 201
    verg = verg_response.json()
    verg_uuid = verg["pid_uuid"]
    
    # Create 2 agendapunten for this vergadering via API
    agp1_data = {
        "organisatie": {
            "gemeente": "gm0363",
            "naam": "Gemeente Amsterdam"
        },
        "dossiertype": "agendapunt",
        "agendapuntnaam": "Agendapunt 1",
        "vergadering": {"id": f"http://localhost:8000/vergaderingen/{verg_uuid}"}
    }
    agp1_response = client.post("/agendapunten", json=agp1_data)
    assert agp1_response.status_code == 201
    agp1 = agp1_response.json()
    
    agp2_data = {
        "organisatie": {
            "gemeente": "gm0363",
            "naam": "Gemeente Amsterdam"
        },
        "dossiertype": "agendapunt",
        "agendapuntnaam": "Agendapunt 2",
        "vergadering": {"id": f"http://localhost:8000/vergaderingen/{verg_uuid}"}
    }
    agp2_response = client.post("/agendapunten", json=agp2_data)
    assert agp2_response.status_code == 201
    agp2 = agp2_response.json()
    
    # Create informatieobject linked to agendapunt 1
    info_data = {
        "webpaginalink": "https://example.com/doc.pdf",
        "organisatie": {
            "gemeente": "gm0363",
            "naam": "Gemeente Amsterdam"
        },
        "titel": "Test Document",
        "wooinformatiecategorie": "c_db4862c3",
        "datumingediend": "2017-02-09",
        "agendapunten": [{"id": agp1["pid"]}]
    }
    info_response = client.post("/informatieobjecten", json=info_data)
    assert info_response.status_code == 201
    info = info_response.json()
    
    # Now GET the vergadering and verify informatieobjecten are included
    get_response = client.get(f"/vergaderingen/{verg_uuid}")
    assert get_response.status_code == 200
    data = get_response.json()
    
    # Verify agendapunten are present
    assert "agendapunten" in data
    assert len(data["agendapunten"]) == 2
    
    # Verify informatieobjecten are present
    assert "informatieobjecten" in data
    assert data["informatieobjecten"] is not None
    assert len(data["informatieobjecten"]) == 1
    assert data["informatieobjecten"][0] == info["pid"]
