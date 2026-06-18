# mini-ori-api

FastAPI + SQLite implementatie op basis van `OAS/mini-ori-koop.yaml`.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

API base path: `/ori-mock`

## Test

```bash
pytest -v
```
