from fastapi import APIRouter
from edugrade.api.endpoint.students import router as students_router

router = APIRouter(prefix="/api")
router.include_router(students_router)