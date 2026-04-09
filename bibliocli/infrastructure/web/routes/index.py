from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter(tags=["Frontend"])

static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

@router.get("/")
async def read_index():
    """
    Serve o Nexus Web HUD principal.
    """
    return FileResponse(os.path.join(static_path, "index.html"))
