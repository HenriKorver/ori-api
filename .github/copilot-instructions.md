# GitHub Copilot Instructions - ORI API

## Project Overview
FastAPI implementation of the Open Raads Informatie (ORI) API for Open Overheid (Dutch governmental open data). This API handles meeting information (vergaderingen), agenda items (agendapunten), and documents (informatieobjecten) from Dutch governmental bodies.

## Architecture

### Dual-ID System (Critical Pattern)
**Every resource has TWO IDs**:
- **`pid`** (string UUID): Public identifier exposed in API responses and used in URL paths
- **`id`** (integer): Internal database primary key for foreign key relationships

**Always**:
- Filter/query by `pid` when accepting user input (e.g., `AgendapuntDB.pid == id`)
- Use internal `id` for database relationships (foreign keys)
- Convert PIDs to internal IDs when filtering related entities (see [agendapunten.py](app/routers/agendapunten.py#L78-L109))

Example from agendapunten GET endpoint:
```python
# Convert vergadering PID to internal ID for filtering
vergadering_statement = select(VergaderingDB.id).where(VergaderingDB.pid == vergadering_id)
internal_id = session.exec(vergadering_statement).first()
statement = statement.where(AgendapuntDB.vergadering_id == internal_id)
```

### Database Layer ([models.py](app/models.py))
- SQLModel models suffixed with `DB` (e.g., `AgendapuntDB`, `VergaderingDB`)
- Organisatie data denormalized into three fields: `organisatie_type`, `organisatie_code`, `organisatie_naam`
- Foreign keys use internal integer IDs: `vergadering_id`, `hoofdagendapunt_id`
- Self-referential relationships use `sa_relationship_kwargs={"remote_side": "ModelDB.id"}`

### Schema Layer ([schemas.py](app/schemas.py))
- Pydantic models for request/response without `DB` suffix
- Three variants per resource: Base, ZonderPid (without pid), and full with pid
- `Organisatie` is a Union type: `Gemeente | Provincie | Waterschap`
- Related resources represented as `VerwijzingNaarResource(id, url)`

### Router Pattern ([routers/](app/routers/))
Every router file implements this structure:
1. **`db_to_schema()` converter** - Transforms DB model to API schema with proper organisatie reconstruction
2. **GET collection** - Returns `PaginatedXList` with next/previous/results
3. **POST** - Creates resource, generates UUID for `pid`, converts related PIDs to internal IDs
4. **GET by id** - Filters by `pid` field
5. **PUT** - Updates existing, validates `pid` existence
6. **DELETE** - Returns `{"message": "Verwijderactie geslaagd"}`

## Development Workflow

### Running the Application
```bash
# Activate venv
source .venv/bin/activate

# Start development server (with auto-reload)
uvicorn app.main:app --reload

# Access at http://localhost:8000/docs (Swagger UI)
```

### Testing
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_main.py::test_create_vergadering -v
```

Tests use in-memory SQLite with `StaticPool` and override `get_session` dependency.

### Database
- SQLite file: `ori_api.db` (auto-created on startup)
- Tables created via `create_db_and_tables()` in [database.py](app/database.py)
- No migrations - fresh schema on each startup during development

## Code Conventions

### Error Responses
Always use Dutch error messages:
```python
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="De gevraagde resource is niet gevonden."
)
```

### Response Models
- List endpoints return `PaginatedXList(next, previous, results)`
- POST returns 201 with created object
- PUT returns 201 (not 200) with updated object
- DELETE returns 200 with success message dict

### Organisatie Handling Pattern
When creating/updating resources:
```python
# Extract from Union type
organisatie = input_schema.organisatie
if isinstance(organisatie, Gemeente):
    org_type, org_code = "gemeente", organisatie.gemeente
elif isinstance(organisatie, Provincie):
    org_type, org_code = "provincie", organisatie.provincie
else:  # Waterschap
    org_type, org_code = "waterschap", organisatie.waterschap
```

When converting DB to schema:
```python
if db_model.organisatie_type == "gemeente":
    organisatie = Gemeente(gemeente=db_model.organisatie_code, naam=db_model.organisatie_naam)
# ... etc
```

### URL Construction
Use `API_SERVER` constant from [database.py](app/database.py):
```python
url=f"{API_SERVER}/agendapunten/{agendapunt.pid}"
```

## Common Pitfalls

1. **Never use `id` in URL paths** - Always use `pid` (UUIDs)
2. **Don't forget PID to ID conversion** - When filtering by related resource, convert PID to internal ID first
3. **Organisatie is always denormalized** - Store type/code/naam separately in DB, reconstruct Union type in schema
4. **Foreign keys are integers** - Not PIDs, not strings
5. **PUT returns 201** - Not 200 (per API spec requirements)

## Key Files Reference
- [app/main.py](app/main.py) - FastAPI app, CORS, pretty JSON response, lifespan DB init
- [app/database.py](app/database.py) - SQLite engine, session dependency, API_SERVER config
- [app/models.py](app/models.py) - SQLModel DB models with relationships
- [app/schemas.py](app/schemas.py) - Pydantic request/response schemas
- [app/routers/agendapunten.py](app/routers/agendapunten.py) - Reference implementation of dual-ID pattern
