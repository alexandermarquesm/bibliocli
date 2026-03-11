from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from src.infrastructure.web.dependencies import get_providers
from src.presentation.controllers.book_controller import BookController

router = APIRouter(prefix="/books", tags=["Books"])

class BookSearchResultDTO(BaseModel):
    source: str
    title: str
    author: Optional[str] = None
    language: str
    link: str
    year: Optional[str] = None
    cover_url: Optional[str] = None

@router.get("/search", response_model=List[BookSearchResultDTO])
def search_books(
    query: str, 
    search_type: str = "book",
    provider_name: str = "all",
    providers = Depends(get_providers)
):
    controller = BookController(providers)
    results = controller.get_search_results(query, search_type, provider_name)
    return results

@router.get("/popular", response_model=List[BookSearchResultDTO])
def get_popular_books(
    provider_name: str = "all",
    providers = Depends(get_providers)
):
    controller = BookController(providers)
    results = controller.get_popular_books(provider_name)
    return results
