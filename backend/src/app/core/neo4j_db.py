from neo4j import GraphDatabase
import os

# variables desde .env
NEO4J_HOST = os.getenv("NEO4J_HOST", "localhost")
NEO4J_PORT = os.getenv("NEO4J_PORT", "7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")

# armamos la URI bolt
NEO4J_URI = f"bolt://{NEO4J_HOST}:{NEO4J_PORT}"


class Neo4jDriver:
    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            cls._driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
        return cls._driver

    @classmethod
    def close_driver(cls):
        if cls._driver:
            cls._driver.close()
            cls._driver = None


def get_session():
    driver = Neo4jDriver.get_driver()
    return driver.session()
