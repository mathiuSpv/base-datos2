import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = f"bolt://{os.getenv('NEO4J_HOST', 'localhost')}:{os.getenv('NEO4J_PORT', '7687')}"
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4jpass")

''' Singleton en Core para toda la app (no crear un driver nuevo cada vez que se hace una nueva request 
    'self.driver' = get_neo4j_driver)'''
_driver = None

def get_neo4j_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
    return _driver

''' Cierre de App cuando se apague, LLAMARLO en shutdown en FastAPI lifespan'''
def close_neo4j_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None