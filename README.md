# ORI API - FastAPI Implementation

FastAPI implementatie van de Open Raads Informatie (ORI) API voor Open Overheid.

## Projectstructuur

```
ori-api/
├── OAS/
│   └── openapi.yaml         # OpenAPI specificatie
├── app/
│   ├── __init__.py
│   ├── main.py              # Hoofd FastAPI applicatie
│   ├── database.py          # Database configuratie
│   ├── models.py            # SQLModel database modellen
│   ├── schemas.py           # Pydantic schemas
│   └── routers/
│       ├── __init__.py
│       ├── agendapunten.py
│       ├── informatieobjecten.py
│       └── vergaderingen.py
├── requirements.txt         # Python dependencies
├── .gitignore
└── README.md
```

## Installatie

1. Maak een virtuele omgeving aan:
```bash
python3 -m venv .venv
source .venv/bin/activate  # Op Linux/Mac
```

2. Installeer de dependencies:
```bash
pip install -r requirements.txt
```

## Gebruik

Start de development server:
```bash
uvicorn app.main:app --reload
```

De API is beschikbaar op: `http://localhost:8000`

API documentatie (Swagger UI): `http://localhost:8000/docs`

Alternative API documentatie (ReDoc): `http://localhost:8000/redoc`

## Structuur

- `app/main.py` - Hoofd FastAPI applicatie
- `app/models.py` - SQLModel database modellen
- `app/database.py` - Database configuratie en sessies
- `app/routers/` - API endpoints (agendapunten, informatieobjecten, vergaderingen)
- `app/schemas.py` - Pydantic schemas voor request/response
