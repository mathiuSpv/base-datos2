from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from edugrade.schemas.neo4j.relations import EquivalentToIn
from edugrade.services.neo4j_graph import get_neo4j_service, Neo4jGraphService
from edugrade.audit.context import AuditContext, get_audit_context
from edugrade.audit.exec import audited
import asyncio

router = APIRouter(prefix="/equivalences", tags=["equivalences"])


async def _neo(callable_, *args, **kwargs):
  return await asyncio.to_thread(callable_, *args, **kwargs)


def get_service() -> Neo4jGraphService:
  return get_neo4j_service()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_equivalence(
  request: Request,
  payload: EquivalentToIn,
  audit: AuditContext = Depends(get_audit_context),
  svc: Neo4jGraphService = Depends(get_service),
):
  audit_logger = request.app.state.audit_logger

  try:
    async def _do():
      return await _neo(
        svc.add_equivalence,
        payload.fromSubjectId,
        payload.toSubjectId,
        payload.levelStage,
      )

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
    raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{subject_id}", status_code=status.HTTP_200_OK)
async def delete_equivalence(
  request: Request,
  subject_id: str,
  levelStage: str = Query(..., min_length=1),
  audit: AuditContext = Depends(get_audit_context),
  svc: Neo4jGraphService = Depends(get_service),
):
  audit_logger = request.app.state.audit_logger

  async def _do():
    result = await _neo(svc.unlink_equivalence_by_subject, subject_id, levelStage)
    if not result["deleted"]:
      raise HTTPException(status_code=404, detail="Subject has no equivalence group for that levelStage")
    return 0

  res = await audited(
    audit_logger=audit_logger,
    audit=audit,
    operation="DELETE",
    db="neo4j",
    entity_type="Equivalence",
    entity_id=f"{subject_id}:{levelStage}",
    payload_summary=f"equivalence delete; subject={subject_id} levelStage={levelStage}",
    fn=_do,
  )

  return {"ok": True, **res}


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