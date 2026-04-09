from fastapi import APIRouter, HTTPException, Depends, Request
import os
import secrets
import json
from bibliocli.infrastructure.web.dependencies import get_providers, get_formatting_agent
from bibliocli.presentation.controllers.book_controller import BookController

router = APIRouter(prefix="/books", tags=["Books"])

@router.get("/download")
async def download_and_format_book(
    url: str,
    request: Request,
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
    
    # Recupera o repositório compartilhado do estado do app
    repo_turso = getattr(request.app.state, "turso_repo", None)
    
    data, error = await controller.get_formatted_book(
        url, formatting_agent, options, repo_turso=repo_turso
    )
    
    if error:
        status_code = 404 if "Índice" in error else 400
        raise HTTPException(status_code=status_code, detail=error)
        
    return data
