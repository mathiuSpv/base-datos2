from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.concurrency import run_in_threadpool

from edugrade.schemas.neo4j.relations import EquivalentToIn
from edugrade.services.neo4j_graph import get_neo4j_service, Neo4jGraphService

from edugrade.audit.context import AuditContext, get_audit_context
from edugrade.audit.exec import audited

router = APIRouter(prefix="/equivalences", tags=["equivalences"])


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

    async def _do():
        # Neo4j service es SYNC -> lo mandamos a threadpool
        return await run_in_threadpool(
            svc.add_equivalence,
            payload.fromSubjectId,
            payload.toSubjectId,
            payload.levelStage,
        )

    try:
        res = await audited(
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
        # Audited ya dejó ERROR; acá mantenemos tu API como 400
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

    async def _do():
        result = await run_in_threadpool(
            svc.unlink_equivalence_by_subject,
            subject_id,
            levelStage,
        )
        if not result.get("deleted"):
            raise HTTPException(
                status_code=404,
                detail="Subject has no equivalence group for that levelStage",
            )
        return result

    result = await audited(
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
def list_equivalences(
    subject_id: str,
    levelStage: str = Query(..., min_length=1),
    svc: Neo4jGraphService = Depends(get_service),
):
    items = svc.get_equivalences_group(subject_id, levelStage)
    if not items:
        return {"subjectId": subject_id, "levelStage": levelStage, "equivalences": []}
    return {"subjectId": subject_id, "levelStage": levelStage, "equivalences": items}