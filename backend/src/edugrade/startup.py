from contextlib import asynccontextmanager
from fastapi import FastAPI

from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import GraphDatabase
from cassandra.cluster import Cluster
import redis.asyncio as redis

from edugrade.config import settings

#Cassandra
from edugrade.audit.schema import ensure_audit_schema
from edugrade.audit.logger import AuditLogger


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo_client = AsyncIOMotorClient(settings.mongo_uri)
    mongo_db = mongo_client[settings.mongo_db]

    neo4j_driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    cass_cluster = Cluster(settings.cassandra_hosts, port=settings.cassandra_port)
    cass_session = cass_cluster.connect()

    ensure_audit_schema(cass_session, settings.cassandra_keyspace)
    app.state.audit_logger = AuditLogger(cass_session, service_name=settings.app_name)

    redis_client = redis.from_url(settings.redis_url, decode_responses=True)

        app.state.mongo_client = mongo_client
        app.state.mongo_db = mongo_db
    except Exception as e:
        print(f"[startup] Mongo disabled: {type(e).__name__}: {e}")

    app.state.neo4j_driver = None
    try:
        app.state.neo4j_driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    except Exception as e:
        print(f"[startup] Neo4j disabled: {type(e).__name__}: {e}")

    app.state.cassandra_cluster = None
    app.state.cassandra_session = None
    try:
        cass_cluster = Cluster(settings.cassandra_hosts, port=settings.cassandra_port)
        cass_session = cass_cluster.connect()
        app.state.cassandra_cluster = cass_cluster
        app.state.cassandra_session = cass_session
    except Exception as e:
        print(f"[startup] Cassandra disabled: {type(e).__name__}: {e}")

    app.state.redis = None
    try:
        app.state.redis = redis.from_url(settings.redis_url, decode_responses=True)
        await app.state.redis.ping()
    except Exception as e:
        print(f"[startup] Redis disabled: {type(e).__name__}: {e}")

    try:
        yield
    finally:
        mongo_client.close()
        if app.state.neo4j_driver:
            app.state.neo4j_driver.close()

        if app.state.cassandra_session:
            app.state.cassandra_session.shutdown()

        if app.state.cassandra_cluster:
            app.state.cassandra_cluster.shutdown()

        if app.state.redis:
            await app.state.redis.close()