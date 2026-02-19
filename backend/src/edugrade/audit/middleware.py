import time
from uuid import uuid4
from fastapi import Request

async def request_context_middleware(request: Request, call_next):
    request.state.request_id = uuid4()

    start = time.perf_counter()
    try:
        response = await call_next(request)
        return response
    finally:
        request.state.latency_ms = int((time.perf_counter() - start) * 1000)
