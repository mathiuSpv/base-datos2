from fastapi import APIRouter
from edugrade.api.endpoint.equivalences import router as equivalences_router

router = APIRouter(prefix="/api")
router.include_router(equivalences_router)