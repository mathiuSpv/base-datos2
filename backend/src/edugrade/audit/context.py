from dataclasses import dataclass
from uuid import UUID
from fastapi import Request

@dataclass(frozen=True)
class AuditContext:
    request_id: UUID
    user_name: str = "default"

def get_audit_context(request: Request) -> AuditContext:
    # request_id lo crea el middleware
    return AuditContext(
        request_id=request.state.request_id,
        user_name="default",
    )