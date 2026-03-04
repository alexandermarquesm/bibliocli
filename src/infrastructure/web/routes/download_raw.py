from fastapi import APIRouter, HTTPException, Depends, Response
import os
import secrets
from src.infrastructure.web.dependencies import get_providers
from src.presentation.controllers.book_controller import BookController

router = APIRouter(prefix="/books", tags=["Books"])

@router.get("/download_raw")
def download_raw_book(
    url: str,
    providers = Depends(get_providers)
):
    controller = BookController(providers)
    content, filename, error = controller.get_raw_book(url)
    
    if error:
        raise HTTPException(status_code=400, detail=error)

    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )
