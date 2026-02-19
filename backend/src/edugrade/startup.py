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

    app.state.neo4j_driver = neo4j_driver

    app.state.cassandra_cluster = cass_cluster
    app.state.cassandra_session = cass_session

    app.state.redis = redis_client

    try:
        yield
    finally:
        mongo_client.close()
        neo4j_driver.close()
        cass_session.shutdown()
        cass_cluster.shutdown()
        await redis_client.close()
