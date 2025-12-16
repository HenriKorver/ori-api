# Implementation Plan: OAS Changes to Python Code

## Overview
Two changes were made to the OpenAPI specification in `OAS/openapi.yaml` that need to be implemented in the Python FastAPI application.

## Change 1: Add Query Parameter to GET /agendapunten

### OAS Change (lines 21-27)
Added `vergadering` query parameter to filter agendapunten by vergadering PID:
```yaml
- name: vergadering
  in: query
  description: Filter op agendapunten behorende bij een specifieke vergadering (PID)
  required: false
  schema:
    type: string
    format: uuid
```

### Implementation Location
File: `app/routers/agendapunten.py`
Function: `get_agendapunten()` (lines 78-91)

### Current Code
```python
@router.get("", response_model=List[Agendapunt])
def get_agendapunten(session: SessionDep):
    """Haal alle agendapunten op."""
    agendapunten = session.exec(select(AgendapuntDB)).all()
    return [db_to_schema(agendapunt) for agendapunt in agendapunten]
```

### Proposed Implementation
```python
@router.get("", response_model=List[Agendapunt])
def get_agendapunten(
    session: SessionDep,
    vergadering: Optional[str] = Query(None, description="Filter op agendapunten behorende bij een specifieke vergadering (PID)")
):
    """Haal alle agendapunten op, optioneel gefilterd op vergadering."""
    query = select(AgendapuntDB)
    
    if vergadering:
        # Find the vergadering by PID
        vergadering_db = session.exec(
            select(VergaderingDB).where(VergaderingDB.pid == vergadering)
        ).first()
        
        if not vergadering_db:
            raise HTTPException(status_code=404, detail="Vergadering niet gevonden")
        
        # Filter agendapunten by vergadering_id
        query = query.where(AgendapuntDB.vergadering_id == vergadering_db.id)
    
    agendapunten = session.exec(query).all()
    return [db_to_schema(agendapunt) for agendapunt in agendapunten]
```

### Required Imports
Ensure these imports are present at the top of `agendapunten.py`:
- `from typing import Optional`
- `from fastapi import Query, HTTPException`
- `from app.models import VergaderingDB` (already imported)

---

## Change 2: Add agendapunten Field to Vergadering Schema

### OAS Change (lines 986-993)
Added `agendapunten` array field to Vergadering schema:
```yaml
agendapunten:
  type: array
  items:
    type: string
    format: uri
  description: URL-referenties naar de agendapunten van deze vergadering
  example:
    - "http://localhost:8000/agendapunten/550e8400-e29b-41d4-a716-446655440001"
```

### Implementation Locations

#### Step 1: Update Schema
File: `app/schemas.py`
Schema: `Vergadering`

Add field to the Vergadering schema:
```python
agendapunten: Optional[List[str]] = None
```

Required import:
```python
from typing import List, Optional
```

#### Step 2: Populate Field in Router
File: `app/routers/vergaderingen.py`
Function: `db_to_schema()`

Current `db_to_schema()` function needs to be modified to:
1. Query all agendapunten related to the vergadering (via `vergadering_id`)
2. Build URI references for each agendapunt
3. Populate the `agendapunten` field

### Proposed Implementation for db_to_schema()
```python
def db_to_schema(vergadering: VergaderingDB, session: Session) -> Vergadering:
    """Converteer database model naar response schema."""
    # Query related agendapunten
    agendapunten = session.exec(
        select(AgendapuntDB).where(AgendapuntDB.vergadering_id == vergadering.id)
    ).all()
    
    # Build URI references
    agendapunten_uris = [
        f"{API_SERVER}/agendapunten/{agendapunt.pid}"
        for agendapunt in agendapunten
    ]
    
    return Vergadering(
        pid=vergadering.pid,
        titel=vergadering.titel,
        datum=vergadering.datum,
        tijdstip=vergadering.tijdstip,
        locatie=vergadering.locatie,
        status=vergadering.status,
        agendapunten=agendapunten_uris
    )
```

### Function Signature Update
All functions calling `db_to_schema()` need to pass the `session` parameter:

**get_vergaderingen():**
```python
return [db_to_schema(vergadering, session) for vergadering in vergaderingen]
```

**get_vergadering():**
```python
return db_to_schema(vergadering, session)
```

**post_vergadering():**
```python
return db_to_schema(new_vergadering, session)
```

**put_vergadering():**
```python
return db_to_schema(vergadering, session)
```

### Required Imports for vergaderingen.py
Ensure these imports are present:
- `from app.models import AgendapuntDB`
- `from sqlmodel import Session, select`

---

## Testing Strategy

### Test Change 1 (Query Parameter)
1. Test GET /agendapunten without filter (should return all)
2. Test GET /agendapunten?vergadering={valid_uuid} (should return filtered)
3. Test GET /agendapunten?vergadering={invalid_uuid} (should return 404)

### Test Change 2 (agendapunten Field)
1. Create vergadering
2. Create 2-3 agendapunten linked to that vergadering
3. GET the vergadering
4. Verify `agendapunten` field contains array of URI strings
5. Verify URIs match the format `http://localhost:8000/agendapunten/{uuid}`

### Integration Test
1. Create vergadering
2. Create agendapunten for that vergadering
3. Use new query parameter to filter: GET /agendapunten?vergadering={vergadering_pid}
4. Verify response contains only agendapunten for that vergadering
5. GET /vergaderingen/{pid} and verify agendapunten array matches filtered results

---

## Dependencies Between Changes
- Changes are **independent** and can be implemented in any order
- No dependencies between the two implementations
- Both changes use existing database relationships (AgendapuntDB.vergadering_id ↔ VergaderingDB.id)

---

## Priority
Both changes are equally important for OAS compliance:
1. **Query parameter** (Change 1): Enables filtering functionality for API consumers
2. **Schema field** (Change 2): Provides navigation from vergadering to related agendapunten

Recommended order: Implement Change 1 first (simpler, single file), then Change 2 (multiple files).

---

## Rollback Plan
If issues arise:
1. Both changes are additive (no breaking changes to existing functionality)
2. Query parameter is optional (defaults to None)
3. agendapunten field is optional in schema
4. Can revert individual files using git: `git checkout HEAD -- <file>`

---

## Notes
- API_SERVER constant is defined in `app/config.py` as `"http://localhost:8000"`
- Database relationship already exists: `AgendapuntDB.vergadering_id` foreign key to `VergaderingDB.id`
- All PIDs are now pure UUIDs (format: `str(uuid.uuid4())`)
- Pretty JSON formatting is already enabled via `PrettyJSONResponse` class
