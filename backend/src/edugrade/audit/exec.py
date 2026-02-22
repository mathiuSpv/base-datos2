from __future__ import annotations

import time
from typing import Any, Awaitable, Callable, Optional

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool

from edugrade.audit.context import AuditContext


async def audit_log(
    audit_logger,
    *,
    operation: str,
    db: str,
    entity_type: str,
    entity_id: str,
    audit: AuditContext,
    status: str,
    payload_summary: str | None = None,
    latency_ms: int | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    """
    audit_logger.log es sync y bloqueante (Cassandra Session.execute).
    Lo corremos en threadpool para no bloquear endpoints async.
    """
    await run_in_threadpool(
        audit_logger.log,
        operation=operation,
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        request_id=audit.request_id,
        user_name=audit.user_name,
        status=status,
        latency_ms=latency_ms,
        error_code=error_code,
        error_message=error_message,
        payload_summary=payload_summary,
    )


async def audited(
    *,
    audit_logger,
    audit: AuditContext,
    operation: str,
    db: str,
    entity_type: str,
    entity_id: str,
    payload_summary: str,
    fn: Callable[[], Awaitable[Any]],
    # opcional: si el id real sale del resultado (CREATE)
    entity_id_from_result: Optional[Callable[[Any], str]] = None,
) -> Any:
    start = time.perf_counter()

    try:
        result = await fn()
        latency_ms = int((time.perf_counter() - start) * 1000)

        final_entity_id = entity_id_from_result(result) if entity_id_from_result else entity_id

        await audit_log(
            audit_logger,
            operation=operation,
            db=db,
            entity_type=entity_type,
            entity_id=final_entity_id,
            audit=audit,
            status="SUCCESS",
            payload_summary=payload_summary,
            latency_ms=latency_ms,
        )
        return result

    except HTTPException as e:
        latency_ms = int((time.perf_counter() - start) * 1000)

        await audit_log(
            audit_logger,
            operation=operation,
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            audit=audit,
            status="ERROR",
            payload_summary=payload_summary,
            latency_ms=latency_ms,
            error_code=f"HTTP_{e.status_code}",
            error_message=str(e.detail)[:500],
        )
        raise

    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)

        await audit_log(
            audit_logger,
            operation=operation,
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            audit=audit,
            status="ERROR",
            payload_summary=payload_summary,
            latency_ms=latency_ms,
            error_code=type(e).__name__,
            error_message=str(e)[:500],
        )
        raise