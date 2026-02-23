import sys
import os
import requests
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.domain.entities import BookSearchResult
from src.application.interfaces import BookSearchProvider

class OpenLibraryProvider(BookSearchProvider):
    def search(self, query: str) -> List[BookSearchResult]:
        results = []
        try:
            r = requests.get(f"https://openlibrary.org/search.json?q={query}&limit=5").json()
            for item in r.get("docs", []):
                langs = item.get("language", [])
                if not langs:
                    lang_str = "Desconhecido"
                else:
                    lang_str = ", ".join(langs[:3])
                
                key = item.get("key", "")
                fulltext = " ✓" if item.get("has_fulltext") else " ✗"
                
                # Traduz do JSON para a nossa Entidade de Domínio Pura
                results.append(BookSearchResult(
                    source="OpenLibrary",
                    title=f"{item.get('title', '')} (Texto Completo:{fulltext})",
                    language=lang_str,
                    link=f"https://openlibrary.org{key}"
                ))
        except Exception:
            pass
        return results

    def search_by_author(self, author: str) -> List[BookSearchResult]:
        results = []
        try:
            r = requests.get(f"https://openlibrary.org/search.json?author={author}&limit=5").json()
            for item in r.get("docs", []):
                langs = item.get("language", [])
                if not langs:
                    lang_str = "Desconhecido"
                else:
                    lang_str = ", ".join(langs[:3])
                
                key = item.get("key", "")
                fulltext = " ✓" if item.get("has_fulltext") else " ✗"
                
                # Traduz do JSON para a nossa Entidade de Domínio Pura
                results.append(BookSearchResult(
                    source="OpenLibrary",
                    title=f"{item.get('title', '')} (Texto Completo:{fulltext})",
                    language=lang_str,
                    link=f"https://openlibrary.org{key}"
                ))
        except Exception:
            pass
        return results
