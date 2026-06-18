from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_db_and_tables
from app.routers import agendapunten, informatieobjecten, vergaderingen


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="De ORI API voor Open Overheid",
    description=(
        "Gegevens uit de Open Raads Informatie systemen kunnen met deze API worden aangeleverd "
        "voor actieve openbaarmaking via Open Overheid."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agendapunten.router, prefix="/ori-mock")
app.include_router(informatieobjecten.router, prefix="/ori-mock")
app.include_router(vergaderingen.router, prefix="/ori-mock")


@app.get("/")
def root():
    return {
        "message": "mini-ori-api",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
