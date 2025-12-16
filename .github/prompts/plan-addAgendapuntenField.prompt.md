# Plan: Add agendapunten Field to Vergadering Schema

Implement the `agendapunten` field on Vergadering responses to provide URL references to related agendapunten, as specified in the OAS schema (lines 979-987).

## OAS Change

Added `agendapunten` array field to Vergadering schema:
```yaml
agendapunten:
  type: array
  items:
    type: string
    format: uri
  description: "URL-referenties naar de agendapunten van deze vergadering."
  title: Agendapunten
  uniqueItems: true
```

## Implementation Steps

### Step 1: Update Schema (app/schemas.py)

Add field to the `VergaderingBase` class (after `deelvergaderingen` field):
```python
agendapunten: Optional[List[str]] = None
```

Ensure imports include:
```python
from typing import List, Optional
```

### Step 2: Update Router (app/routers/vergaderingen.py)

Modify the `db_to_schema()` function to populate the `agendapunten` field:

**Current code** (lines 20-76):
```python
def db_to_schema(db_vergadering: VergaderingDB) -> Vergadering:
    """Convert database model to schema"""
    # ... existing logic ...
    
    return Vergadering(
        pid=db_vergadering.pid,
        webpaginalink=db_vergadering.webpaginalink,
        organisatie=organisatie,
        dossiertype=db_vergadering.dossiertype,
        naam=db_vergadering.naam,
        aanvang=db_vergadering.aanvang,
        hoofdvergadering=hoofdvergadering_ref,
        einde=db_vergadering.einde,
        georganiseerddoorgremium=gremium,
        geplandeaanvang=db_vergadering.geplandeaanvang,
        geplandeeinde=db_vergadering.geplandeeinde,
        geplandedatum=db_vergadering.geplandedatum,
        locatie=db_vergadering.locatie,
        vergaderstatus=db_vergadering.vergaderstatus,
        vergadertoelichting=db_vergadering.vergadertoelichting,
        vergaderdatum=db_vergadering.vergaderdatum,
        vergaderingstype=db_vergadering.vergaderingstype,
    )
```

**New implementation:**
```python
def db_to_schema(db_vergadering: VergaderingDB) -> Vergadering:
    """Convert database model to schema"""
    # ... existing logic ...
    
    # Build agendapunten URI references
    agendapunten_uris = [
        f"{API_SERVER}/agendapunten/{agendapunt.pid}"
        for agendapunt in db_vergadering.agendapunten
    ] if db_vergadering.agendapunten else []
    
    return Vergadering(
        pid=db_vergadering.pid,
        webpaginalink=db_vergadering.webpaginalink,
        organisatie=organisatie,
        dossiertype=db_vergadering.dossiertype,
        naam=db_vergadering.naam,
        aanvang=db_vergadering.aanvang,
        hoofdvergadering=hoofdvergadering_ref,
        einde=db_vergadering.einde,
        georganiseerddoorgremium=gremium,
        geplandeaanvang=db_vergadering.geplandeaanvang,
        geplandeeinde=db_vergadering.geplandeeinde,
        geplandedatum=db_vergadering.geplandedatum,
        locatie=db_vergadering.locatie,
        vergaderstatus=db_vergadering.vergaderstatus,
        vergadertoelichting=db_vergadering.vergadertoelichting,
        vergaderdatum=db_vergadering.vergaderdatum,
        vergaderingstype=db_vergadering.vergaderingstype,
        agendapunten=agendapunten_uris,
    )
```

Ensure `API_SERVER` is imported:
```python
from app.database import API_SERVER
```

### Step 3: Update Tests (tests/test_main.py)

Add test to verify the `agendapunten` field:

```python
def test_vergadering_includes_agendapunten_references():
    """Test that a vergadering response includes references to its agendapunten."""
    # Create vergadering
    vergadering_data = {
        "organisatie": {"gemeente": "GM0363", "naam": "Amsterdam"},
        "naam": "Raadsvergadering",
        "dossiertype": "vergadering"
    }
    response = client.post("/vergaderingen", json=vergadering_data)
    assert response.status_code == 201
    vergadering_pid = response.json()["pid"]
    
    # Create 2 agendapunten linked to this vergadering
    agendapunt_pids = []
    for i in range(2):
        agendapunt_data = {
            "organisatie": {"gemeente": "GM0363", "naam": "Amsterdam"},
            "vergadering": f"{API_SERVER}/vergaderingen/{vergadering_pid}",
            "agendapuntnummer": f"{i+1}",
            "onderwerp": f"Agendapunt {i+1}"
        }
        response = client.post("/agendapunten", json=agendapunt_data)
        assert response.status_code == 201
        agendapunt_pids.append(response.json()["pid"])
    
    # Get vergadering and verify agendapunten field
    response = client.get(f"/vergaderingen/{vergadering_pid}")
    assert response.status_code == 200
    data = response.json()
    
    assert "agendapunten" in data
    assert len(data["agendapunten"]) == 2
    
    # Verify format of URIs
    for uri in data["agendapunten"]:
        assert uri.startswith(f"{API_SERVER}/agendapunten/")
        # Extract PID and verify it's a valid UUID
        pid = uri.split("/")[-1]
        assert pid in agendapunt_pids
```

## Technical Details

### Database Relationship
The `VergaderingDB` model already has the relationship defined:
```python
agendapunten: List["AgendapuntDB"] = Relationship(back_populates="vergadering")
```

This means `db_vergadering.agendapunten` will automatically give us all related agendapunten records.

### API Server Configuration
`API_SERVER` is defined in `app/database.py`:
```python
API_SERVER = os.getenv("API_SERVER", "http://localhost:8000")
```

### URI Format
- OAS specifies `format: uri` for full URIs
- Example: `http://localhost:8000/agendapunten/550e8400-e29b-41d4-a716-446655440001`
- Note: Agendapunten currently use relative URLs for vergadering references, but OAS explicitly wants full URIs for this field

## Design Decisions

### Empty List vs Null
When a vergadering has no agendapunten:
- Option 1: Return empty array `[]`
- Option 2: Return `null`
- Option 3: Omit the field entirely

**Recommendation:** Return empty array `[]` for consistency and easier client handling. The field is optional in the schema (not in `required` list), but returning an empty array is more explicit and prevents null checks on the client side.

### Performance Considerations
- The SQLModel relationship uses lazy loading by default
- May cause N+1 query issues if fetching many vergaderingen
- For production, consider using `selectinload()` or `joinedload()` from SQLAlchemy if performance becomes an issue
- Current implementation is fine for the mock API use case

## Testing Strategy

1. Test vergadering with no agendapunten (should return empty array)
2. Test vergadering with multiple agendapunten (should return array of URIs)
3. Verify URI format matches `{API_SERVER}/agendapunten/{pid}`
4. Verify all linked agendapunten are included
5. Test that creating/deleting agendapunten updates the field correctly

## Rollback Plan

If issues arise:
- Change is additive and non-breaking
- Field is optional (not in `required` list)
- Can revert files using: `git checkout HEAD -- app/schemas.py app/routers/vergaderingen.py`
- Existing tests should continue to pass (field is optional)

## Dependencies

- No new package dependencies required
- Uses existing SQLModel relationships
- Uses existing `API_SERVER` constant
- All required infrastructure already in place
