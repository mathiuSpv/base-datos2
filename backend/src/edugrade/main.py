from fastapi import FastAPI, Request
from edugrade.config import settings
from edugrade.startup import lifespan
from edugrade.api.router import router as api_router

app = FastAPI(
    title=settings.app_name, 
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
app.include_router(api_router)


@app.get("/health")
async def health(request: Request):
    results: dict[str, object] = {}

    # Mongo
    try:
        await request.app.state.mongo_client.admin.command("ping")
        results["mongo"] = "ok"
    except Exception as e:
        results["mongo"] = {"type": type(e).__name__, "message": str(e), "repr": repr(e)}

    # Neo4j
    try:
        with request.app.state.neo4j_driver.session() as session:
            session.run("RETURN 1").single()
        results["neo4j"] = "ok"
    except Exception as e:
        results["neo4j"] = {"type": type(e).__name__, "message": str(e), "repr": repr(e)}

    # Cassandra
    try:
        row = request.app.state.cassandra_session.execute("SELECT now() FROM system.local").one()
        _ = row[0] if row else None
        results["cassandra"] = "ok"
    except Exception as e:
        results["cassandra"] = {"type": type(e).__name__, "message": str(e), "repr": repr(e)}

    # Redis
    try:
        pong = await request.app.state.redis.ping()
        results["redis"] = "ok" if pong else "error: ping_failed"
    except Exception as e:
        results["redis"] = {"type": type(e).__name__, "message": str(e), "repr": repr(e)}

    status_values = list(results.values())

    if all(v == "ok" for v in status_values):
        status = "ok"
    elif all(v != "ok" for v in status_values):
        status = "off"
    else:
        status = "degraded"

    payload = {"status": status, "checks": results}
    if status == "ok":
        payload["app"] = settings.app_name

    return payload