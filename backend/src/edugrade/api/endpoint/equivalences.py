from fastapi import APIRouter, Depends, HTTPException, status, Query
from edugrade.schemas.neo4j.relations import EquivalentToIn
from edugrade.services.neo4j_graph import get_neo4j_service, Neo4jGraphService
import asyncio

router = APIRouter(prefix="/equivalences", tags=["equivalences"])

async def _neo(callable_, *args, **kwargs):
    return await asyncio.to_thread(callable_, *args, **kwargs)

def get_service() -> Neo4jGraphService:
    return get_neo4j_service()

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_equivalence(payload: EquivalentToIn, svc: Neo4jGraphService = Depends(get_service)):
    try:
        res = await _neo(svc.add_equivalence, payload.fromSubjectId, payload.toSubjectId, payload.levelStage)
        return {"ok": True, **res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{subject_id}", status_code=status.HTTP_200_OK)
async def delete_equivalence(
    subject_id: str,
    levelStage: str = Query(..., min_length=1),
    svc: Neo4jGraphService = Depends(get_service),
):
    try:
        result = await _neo(svc.unlink_equivalence_by_subject, subject_id, levelStage)
        if not result["deleted"]:
            raise HTTPException(status_code=404, detail="Subject has no equivalence group for that levelStage")
        return {"ok": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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