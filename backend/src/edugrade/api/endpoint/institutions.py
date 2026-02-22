from fastapi import APIRouter, Depends, HTTPException

from edugrade.services.neo4j_graph import get_neo4j_service, Neo4jGraphService
from edugrade.schemas.neo4j_subject import SubjectOut

router = APIRouter(prefix="/institutions", tags=["Institutions"])


def svc_dep() -> Neo4jGraphService:
    return get_neo4j_service()


@router.get("/{institutionMongoId}/subjects", response_model=list[SubjectOut])
def get_subjects_by_institution(
    institutionMongoId: str,
    svc: Neo4jGraphService = Depends(svc_dep),
):
    try:
        return svc.get_subjects_by_institution(institutionMongoId)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))