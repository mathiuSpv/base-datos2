from fastapi import FastAPI, Request, HTTPException
from edugrade.config import settings
from edugrade.startup import lifespan

app = FastAPI(title=settings.app_name, lifespan=lifespan)

@app.get("/health")
async def health(request: Request):
    results = {}

    try:
        await request.app.state.mongo_client.admin.command("ping")
        results["mongo"] = "ok"
    except Exception as e:
        results["mongo"] = {
            "type": type(e).__name__,
            "message": str(e),
            "repr": repr(e),
        }

    try:
        with request.app.state.neo4j_driver.session() as session:
            session.run("RETURN 1").single()
        results["neo4j"] = "ok"
    except Exception as e:
        results["neo4j"] = {
            "type": type(e).__name__,
            "message": str(e),
            "repr": repr(e),
        }

    try:
        row = request.app.state.cassandra_session.execute("SELECT now() FROM system.local").one()
        _ = row[0] if row else None
        results["cassandra"] = "ok"
    except Exception as e:
        results["cassandra"] = {
            "type": type(e).__name__,
            "message": str(e),
            "repr": repr(e),
        }
        
    try:
        pong = await request.app.state.redis.ping()
        results["redis"] = "ok" if pong else "error: ping_failed"
    except Exception as e:
        results["redis"] = {
            "type": type(e).__name__,
            "message": str(e),
            "repr": repr(e),
        }

    if any(v != "ok" for v in results.values()):
        raise HTTPException(status_code=503, detail={"status": "degraded", "checks": results})

    return {"status": "ok", "app": settings.app_name, "checks": results}
