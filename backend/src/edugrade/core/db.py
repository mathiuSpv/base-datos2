from typing import Any
from fastapi import Request

def get_mongo_db(request: Request) -> Any:
    return request.app.state.mongo_db
