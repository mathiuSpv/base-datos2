from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from edugrade.core.db import get_mongo_db
from edugrade.schemas.mongo.dashboard import DashboardOut, DashboardSubjectsOut
from edugrade.services.mongo.dashboard import DashboardService
from edugrade.services.neo4j_graph import get_neo4j_service, Neo4jGraphService


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_service(
  request: Request,
  db=Depends(get_mongo_db),
  neo: Neo4jGraphService = Depends(get_neo4j_service),
) -> DashboardService:
  return DashboardService(db, request.app.state.audit_logger, neo)


@router.get("", response_model=DashboardOut)
async def get_dashboard(
  country: str = Query(..., min_length=3, max_length=3, description="ISO-3 country code, e.g. ARG"),
  institutionId: str | None = Query(default=None, description="Optional institution ObjectId hex"),
  targetSystem: str | None = Query(
    default=None,
    description="None => ZA; 'ZA' => ZA; other => convert from ZA to that system",
  ),
  svc: DashboardService = Depends(get_service),
):
  return await svc.get_average(country=country, institution_id=institutionId, target_system=targetSystem)


@router.get("/subjects", response_model=DashboardSubjectsOut)
async def get_dashboard_by_subject(
  country: str = Query(..., min_length=3, max_length=3, description="ISO-3 country code, e.g. ARG"),
  institutionId: str = Query(..., description="Institution ObjectId hex (required for subjects breakdown)"),
  targetSystem: str | None = Query(
    default=None,
    description="None => ZA; 'ZA' => ZA; other => convert from ZA to that system",
  ),
  svc: DashboardService = Depends(get_service),
):
  return await svc.get_average_by_subject(country=country, institution_id=institutionId, target_system=targetSystem)