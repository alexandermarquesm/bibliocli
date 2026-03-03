from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import os
import secrets
import json

from src.infrastructure.web.dependencies import get_providers, get_formatting_agent

router = APIRouter(prefix="/books", tags=["Books"])

class BookSearchResultDTO(BaseModel):
    source: str
    title: str
    language: str
    link: str

@router.get("/search", response_model=List[BookSearchResultDTO])
def search_books(
    query: str, 
    search_type: str = "book",
    providers = Depends(get_providers)
):
    results = []
    for provider in providers:
        try:
             if search_type == "author":
                 provider_results = provider.search_by_author(query)
             else:
                 provider_results = provider.search(query)
                 
             for res in provider_results:
                 results.append(BookSearchResultDTO(
                     source=res.source,
                     title=res.title,
                     language=res.language,
                     link=res.link
                 ))
        except Exception as e:
            print(f"Erro ao pesquisar em {provider.__class__.__name__}: {e}")
            
    return results

@router.get("/download")
def download_and_format_book(
    url: str,
    include_paragraphs: bool = True,
    only_metadata: bool = False,
    chapter_index: int = None,
    providers = Depends(get_providers),
    formatting_agent = Depends(get_formatting_agent)
):
    provider = next((p for p in providers if hasattr(p, 'can_download') and p.can_download(url)), None)
    
    if not provider:
         raise HTTPException(status_code=400, detail="Nenhum provedor suporta o download desta URL.")
         
    tmp_path = f"/tmp/bibliocli_temp_{secrets.token_hex(4)}.txt"
    
    try:
        success = provider.download(url, tmp_path)
        if not success:
            raise HTTPException(status_code=500, detail="Falha ao baixar texto bruto do provedor.")
            
        with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
            
        source_name = provider.__class__.__name__
        book_info = provider.get_info(url)
        title = book_info.title if book_info else "Título Desconhecido"
        author = book_info.author if book_info else "Autor Desconhecido"
        
        formatted_json_string = formatting_agent.format_text(
            raw_text, 
            source_name,
            title=title,
            author=author
        )
        
        try:
            formatted_data = json.loads(formatted_json_string)
            
            # Lógica de Otimização de Resposta
            if "chapters" in formatted_data:
                # Se pediu um capítulo específico (Lazy Loading)
                if chapter_index is not None:
                    if 0 <= chapter_index < len(formatted_data["chapters"]):
                        formatted_data["chapters"] = [formatted_data["chapters"][chapter_index]]
                    else:
                        raise HTTPException(status_code=404, detail="Índice de capítulo fora do intervalo.")
                
                # Se não quer parágrafos (apenas Sumário)
                elif only_metadata or not include_paragraphs:
                    for chapter in formatted_data["chapters"]:
                        chapter["paragraphs"] = []
                        
        except HTTPException:
            raise
        except Exception:
            formatted_data = {"raw_agent_response": formatted_json_string}
            
        return {
            "book_url": url,
            "formatted_content": formatted_data
        }
        
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
