import sys
import os
import requests
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.domain.entities import BookSearchResult
from src.application.interfaces import BookSearchProvider

class WikisourceProvider(BookSearchProvider):
    def search(self, query: str) -> List[BookSearchResult]:
        results = []
        headers = {'User-Agent': 'MeuLeitorApp/1.0 (dev@exemplo.com)'}
        
        # Buscar em PT
        try:
            r_pt = requests.get(
                "https://pt.wikisource.org/w/api.php",
                params={"action": "query", "list": "search", "srsearch": query, "format": "json"},
                headers=headers
            ).json()
            for item in r_pt.get("query", {}).get("search", [])[:3]:
                title = item["title"]
                
                # Traduz do JSON para a Entidade de Domínio Pura
                results.append(BookSearchResult(
                    source="Wikisource (PT)",
                    title=title,
                    language="pt-br",
                    link=f"https://pt.wikisource.org/wiki/{title.replace(' ', '_')}"
                ))
        except Exception:
            pass
        
        # Buscar em EN
        try:
            r_en = requests.get(
                "https://en.wikisource.org/w/api.php",
                params={"action": "query", "list": "search", "srsearch": query, "format": "json"},
                headers=headers
            ).json()
            for item in r_en.get("query", {}).get("search", [])[:3]:
                title = item["title"]
                
                # Traduz do JSON para a Entidade de Domínio Pura
                results.append(BookSearchResult(
                    source="Wikisource (EN)",
                    title=title,
                    language="en",
                    link=f"https://en.wikisource.org/wiki/{title.replace(' ', '_')}"
                ))
        except Exception:
            pass
            
        return results

    def search_by_author(self, author: str) -> List[BookSearchResult]:
        """No Wikisource a busca textual já funciona para cruzar nomes de autores com obras."""
        return self.search(author)
