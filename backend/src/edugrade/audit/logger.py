from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, date
from uuid import UUID, uuid4

from cassandra.cluster import Session
from cassandra.query import PreparedStatement

@dataclass
class AuditEvent:
    ts: datetime
    event_id: UUID
    operation: str
    db: str
    entity_type: str
    entity_id: str
    user_name: str
    service: str
    request_id: UUID
    status: str
    latency_ms: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    payload_summary: str | None = None

class AuditLogger:
    def __init__(self, session: Session, service_name: str):
        self.session = session
        self.service_name = service_name

        # prepared statements (más rápido y prolijo)
        self._ins_entity: PreparedStatement = session.prepare("""
            INSERT INTO audit_by_entity (
              entity_type, entity_id, ts, event_id, operation, db,
              user_name, service, request_id, status, latency_ms,
              error_code, error_message, payload_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        self._ins_day: PreparedStatement = session.prepare("""
            INSERT INTO audit_by_day (
              day, ts, event_id, operation, db, entity_type, entity_id,
              user_name, service, request_id, status, latency_ms,
              error_code, payload_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        self._ins_req: PreparedStatement = session.prepare("""
            INSERT INTO audit_by_request (
              request_id, ts, event_id, operation, db, entity_type, entity_id,
              user_name, service, status, latency_ms, error_code, error_message, payload_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        self._sel_entity = session.prepare("""
            SELECT * FROM audit_by_entity
            WHERE entity_type = ? AND entity_id = ?
            LIMIT ?
        """)

        self._sel_day = session.prepare("""
            SELECT * FROM audit_by_day
            WHERE day = ?
            LIMIT ?
        """)

        self._sel_request = session.prepare("""
            SELECT * FROM audit_by_request
            WHERE request_id = ?
            LIMIT ?
        """)

    def log(
        self,
        *,
        operation: str,
        db: str,
        entity_type: str,
        entity_id: str,
        request_id: UUID,
        user_name: str = "default",
        status: str = "SUCCESS",
        latency_ms: int | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        payload_summary: str | None = None,
        ts: datetime | None = None,
    ) -> UUID:
        ts = ts or datetime.now(timezone.utc)
        event_id = uuid4()
        day = date.fromisoformat(ts.date().isoformat())

        ev = AuditEvent(
            ts=ts,
            event_id=event_id,
            operation=operation,
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            user_name=user_name,
            service=self.service_name,
            request_id=request_id,
            status=status,
            latency_ms=latency_ms,
            error_code=error_code,
            error_message=error_message,
            payload_summary=payload_summary,
        )

        # 3 inserts para soportar 3 “vistas” de consulta
        self.session.execute(self._ins_entity, (
            ev.entity_type, ev.entity_id, ev.ts, ev.event_id, ev.operation, ev.db,
            ev.user_name, ev.service, ev.request_id, ev.status, ev.latency_ms,
            ev.error_code, ev.error_message, ev.payload_summary
        ))

        self.session.execute(self._ins_day, (
            day, ev.ts, ev.event_id, ev.operation, ev.db, ev.entity_type, ev.entity_id,
            ev.user_name, ev.service, ev.request_id, ev.status, ev.latency_ms,
            ev.error_code, ev.payload_summary
        ))

        self.session.execute(self._ins_req, (
            ev.request_id, ev.ts, ev.event_id, ev.operation, ev.db, ev.entity_type, ev.entity_id,
            ev.user_name, ev.service, ev.status, ev.latency_ms, ev.error_code, ev.error_message,
            ev.payload_summary
        ))

        return event_id

    def list_by_entity(self, entity_type: str, entity_id: str, limit: int = 50):
        return list(self.session.execute(self._sel_entity, (entity_type, entity_id, limit)))

    def list_by_day(self, day: date, limit: int = 200):
        return list(self.session.execute(self._sel_day, (day, limit)))

    def list_by_request(self, request_id: UUID, limit: int = 200):
        return list(self.session.execute(self._sel_request, (request_id, limit)))
