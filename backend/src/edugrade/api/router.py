from fastapi import APIRouter
from edugrade.api.endpoint.students import router as students_router
from edugrade.audit.routes import router as audit_router

router = APIRouter(prefix="/api")
router.include_router(students_router)
router.include_router(audit_router)