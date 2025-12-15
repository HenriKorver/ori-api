from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.database import create_db_and_tables
from app.routers import agendapunten, informatieobjecten, vergaderingen


class PrettyJSONResponse(JSONResponse):
    """Custom JSON response with indentation"""
    media_type = "application/json"
    
    def render(self, content) -> bytes:
        import json
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            separators=(", ", ": "),
        ).encode("utf-8")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    create_db_and_tables()
    yield


app = FastAPI(
    title="De ORI API voor Open Overheid",
    description="""Gegevens uit de Open Raads Informatie systemen kunnen met deze API worden aangeleverd voor actieve openbaarmaking via Open Overheid. 
    Ook kan deze API gebruikt worden om aangeleverde data bij te werken. Deze versie van deze API zal naast documentobjecten ook vergader-informatie kunnen 
    verwerken volgens het ontwerp van de VNG mini-ORI API, en daarbij ook een endpoint voor Vergaderingen en Agendapunten ontsluiten.""",
    version="0.1.0",
    contact={
        "url": "https://gitlab.com/koop/woo/aanleveren-ori",
    },
    license_info={
        "name": "European Union Public License, version 1.2 (EUPL-1.2)",
        "url": "https://eupl.eu/1.2/nl/",
    },
    servers=[
        {"url": "http://127.0.0.1:8000", "description": "Local development server"}
    ],
    lifespan=lifespan,
    default_response_class=PrettyJSONResponse,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agendapunten.router)
app.include_router(informatieobjecten.router)
app.include_router(vergaderingen.router)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "ORI API voor Open Overheid",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }
