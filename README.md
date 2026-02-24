# EduGrade Global – Backend

Stack:
- FastAPI + Uvicorn (host)
- MongoDB (Docker)
- Neo4j (Docker)
- Cassandra (Docker)

## 1) Levantar las 4 DB
```bash
docker compose -f docker/compose.yml up -d
docker compose -f docker/compose.yml ps
```

## 2) Crear entorno py
```bash
cd backend
uv venv --python 3.11
```

## 3) Activar env
```bash
.venv\Scripts\activate
```

## 4) Syncronizar
```bash
uv sync
```

## 5) Levantar el Backend
```bash
uv run uvicorn edugrade.main:app --reload --app-dir src
```

## 6) Populate de Datos
```bash
python docker/seed/api_caller.py --base-url http://localhost:8000 --seed 123  
```