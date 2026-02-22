from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.concurrency import run_in_threadpool

from edugrade.schemas.neo4j.relations import EquivalentToIn
from edugrade.services.neo4j_graph import get_neo4j_service, Neo4jGraphService
import asyncio

from edugrade.audit.context import AuditContext, get_audit_context
from edugrade.audit.exec import audited

router = APIRouter(prefix="/equivalences", tags=["equivalences"])

async def _neo(callable_, *args, **kwargs):
    return await asyncio.to_thread(callable_, *args, **kwargs)

def get_service() -> Neo4jGraphService:
    return get_neo4j_service()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_equivalence(
    payload: EquivalentToIn,
    audit: AuditContext = Depends(get_audit_context),
    svc: Neo4jGraphService = Depends(get_service),
    request: Request = None,
):
    audit_logger = request.app.state.audit_logger

    

    try:
        res = await _neo(svc.add_equivalence, payload.fromSubjectId, payload.toSubjectId, payload.levelStage)
        await audited(
            audit_logger=audit_logger,
            audit=audit,
            operation="CREATE",
            db="neo4j",
            entity_type="Equivalence",
            entity_id=f"{payload.fromSubjectId}->{payload.toSubjectId}:{payload.levelStage}",
            payload_summary=(
                "equivalence create; "
                f"from={payload.fromSubjectId} to={payload.toSubjectId} levelStage={payload.levelStage}"
            ),
            fn=_do,
        )
        return {"ok": True, **res}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{subject_id}", status_code=status.HTTP_200_OK)
async def delete_equivalence(
    subject_id: str,
    levelStage: str = Query(..., min_length=1),
    audit: AuditContext = Depends(get_audit_context),
    svc: Neo4jGraphService = Depends(get_service),
    request: Request = None,
):
    audit_logger = request.app.state.audit_logger
    result = await _neo(svc.unlink_equivalence_by_subject, subject_id, levelStage)
    if not result["deleted"]:
        raise HTTPException(status_code=404, detail="Subject has no equivalence group for that levelStage")
    await audited(
        audit_logger=audit_logger,
        audit=audit,
        operation="DELETE",
        db="neo4j",
        entity_type="Equivalence",
        entity_id=f"{subject_id}:{levelStage}",
        payload_summary=f"equivalence delete; subject={subject_id} levelStage={levelStage}",
        fn=_do,
    )
    return {"ok": True, **result}

@router.get("/{subject_id}")
async def list_equivalences(
    subject_id: str,
    levelStage: str = Query(..., min_length=1),
    svc: Neo4jGraphService = Depends(get_service),
):
    items = await _neo(svc.get_equivalences_group, subject_id, levelStage)
    if not items:
        return {"subjectId": subject_id, "levelStage": levelStage, "equivalences": []}
    return {"subjectId": subject_id, "levelStage": levelStage, "equivalences": items}