from cassandra.cluster import Session

DDL = [
    # Keyspace
    """
    CREATE KEYSPACE IF NOT EXISTS {ks}
    WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}};
    """,

    # Timeline por entidad
    """
    CREATE TABLE IF NOT EXISTS {ks}.audit_by_entity (
      entity_type      text,
      entity_id        text,
      ts               timestamp,
      event_id         uuid,
      operation        text,
      db               text,
      user_name        text,
      service          text,
      request_id       uuid,
      status           text,
      latency_ms       int,
      error_code       text,
      error_message    text,
      payload_summary  text,
      PRIMARY KEY ((entity_type, entity_id), ts, event_id)
    ) WITH CLUSTERING ORDER BY (ts DESC);
    """,

    # Feed diario
    """
    CREATE TABLE IF NOT EXISTS {ks}.audit_by_day (
      day              date,
      ts               timestamp,
      event_id         uuid,
      operation        text,
      db               text,
      entity_type      text,
      entity_id        text,
      user_name        text,
      service          text,
      request_id       uuid,
      status           text,
      latency_ms       int,
      error_code       text,
      payload_summary  text,
      PRIMARY KEY ((day), ts, event_id)
    ) WITH CLUSTERING ORDER BY (ts DESC);
    """,

    # Por request_id
    """
    CREATE TABLE IF NOT EXISTS {ks}.audit_by_request (
      request_id       uuid,
      ts               timestamp,
      event_id         uuid,
      operation        text,
      db               text,
      entity_type      text,
      entity_id        text,
      user_name        text,
      service          text,
      status           text,
      latency_ms       int,
      error_code       text,
      error_message    text,
      payload_summary  text,
      PRIMARY KEY ((request_id), ts, event_id)
    ) WITH CLUSTERING ORDER BY (ts DESC);
    """,
]

def ensure_audit_schema(session: Session, keyspace: str) -> None:
    for stmt in DDL:
        session.execute(stmt.format(ks=keyspace))

    # Setear keyspace para queries sin prefijo
    session.set_keyspace(keyspace)
