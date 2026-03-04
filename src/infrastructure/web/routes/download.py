from fastapi import APIRouter, HTTPException, Depends
import os
import secrets
import json
from src.infrastructure.web.dependencies import get_providers, get_formatting_agent
from src.presentation.controllers.book_controller import BookController

router = APIRouter(prefix="/books", tags=["Books"])

@router.get("/download")
def download_and_format_book(
    url: str,
    include_paragraphs: bool = True,
    only_metadata: bool = False,
    chapter_index: int = None,
    providers = Depends(get_providers),
    formatting_agent = Depends(get_formatting_agent)
):
    controller = BookController(providers)
    options = {
        "include_paragraphs": include_paragraphs,
        "only_metadata": only_metadata,
        "chapter_index": chapter_index
    }
    
    data, error = controller.get_formatted_book(url, formatting_agent, options)
    
    if error:
        status_code = 404 if "Índice" in error else 400
        raise HTTPException(status_code=status_code, detail=error)
        
    return data
