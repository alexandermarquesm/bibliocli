from fastapi import APIRouter, HTTPException, Depends, Response
import os
import secrets
from bibliocli.infrastructure.web.dependencies import get_providers
from bibliocli.presentation.controllers.book_controller import BookController

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

    media_type = "text/plain"
    if content.startswith(b'PK\x03\x04'):
        media_type = "application/epub+zip"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )
