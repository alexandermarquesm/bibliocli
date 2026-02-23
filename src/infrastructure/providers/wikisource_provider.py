import sys
import os
import requests
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.domain.entities import BookSearchResult
from src.application.interfaces import BookSearchProvider, BookDownloadProvider

class WikisourceProvider(BookSearchProvider, BookDownloadProvider):
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

    def can_download(self, url: str) -> bool:
        return "wikisource.org/wiki/" in url

    def _clean_html(self, html: str) -> str:
        """Remove tags HTML simples para extrair o texto."""
        import re
        # Remove tags script e style
        text = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove todas as outras tags
        text = re.sub(r'<.*?>', ' ', text)
        # Normaliza espaços
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def download(self, url: str, destiny_path: str) -> bool:
        """
        Baixa o texto do Wikisource. Usa a API de 'parse' para garantir que 
        conteúdos transcluidos (comuns em livros) sejam processados corretamente.
        """
        import urllib.parse
        try:
            # Extrair e decodificar título
            title_quoted = url.split("/wiki/")[-1]
            title = urllib.parse.unquote(title_quoted)
            domain = "pt" if "pt.wikisource.org" in url else "en"
            
            headers = {'User-Agent': 'MeuLeitorApp/1.0 (dev@exemplo.com)'}
            api_url = f"https://{domain}.wikisource.org/w/api.php"
            
            # 1. Tentar obter o conteúdo da página principal via Parse
            # Parse resolve transclusões <pages /> que o extracts as vezes ignora
            params_main = {
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json",
                "disablelimitreport": 1
            }
            r_main = requests.get(api_url, params=params_main, headers=headers).json()
            main_html = r_main.get("parse", {}).get("text", {}).get("*", "")
            full_content = self._clean_html(main_html)
            
            # 2. Buscar subpáginas (capítulos/partes)
            params_sub = {
                "action": "query",
                "list": "allpages",
                "apprefix": f"{title}/",
                "apnamespace": 0,
                "aplimit": "max",
                "format": "json"
            }
            r_sub = requests.get(api_url, params=params_sub, headers=headers).json()
            subpages = r_sub.get("query", {}).get("allpages", [])
            
            if subpages:
                print(f"Detectados {len(subpages)} capítulos/partes em '{title}'. Mesclando...")
                
                for sub in subpages:
                    sub_title = sub["title"]
                    params_sub_get = {
                        "action": "parse",
                        "page": sub_title,
                        "prop": "text",
                        "format": "json"
                    }
                    r_sub_res = requests.get(api_url, params=params_sub_get, headers=headers).json()
                    sub_html = r_sub_res.get("parse", {}).get("text", {}).get("*", "")
                    sub_text = self._clean_html(sub_html)
                    
                    if sub_text:
                        full_content += f"\n\n--- {sub_title} ---\n\n"
                        full_content += sub_text
            
            # Validação: Se após o parse o conteúdo for irrelevante
            if not full_content or len(full_content) < 500:
                 print(f"Aviso: O conteúdo de '{title}' parece ser apenas um portal ou índice vazio.")
                 return False

            with open(destiny_path, "w", encoding="utf-8") as f:
                f.write(full_content)
            return True

        except Exception as e:
            print(f"Erro ao processar capítulos do Wikisource: {e}")
            
        return False

    def get_info(self, url: str) -> BookSearchResult:
        title = url.split("/wiki/")[-1].replace("_", " ")
        domain = "PT" if "pt.wikisource.org" in url else "EN"
        return BookSearchResult(
            source=f"Wikisource ({domain})",
            title=title,
            language="pt" if domain == "PT" else "en",
            link=url
        )
