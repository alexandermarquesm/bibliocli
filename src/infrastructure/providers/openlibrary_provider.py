import sys
import os
import requests
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.domain.entities import BookSearchResult
from src.application.interfaces import BookSearchProvider, BookDownloadProvider

class OpenLibraryProvider(BookSearchProvider, BookDownloadProvider):
    def search(self, query: str) -> List[BookSearchResult]:
        results = []
        try:
            r = requests.get(f"https://openlibrary.org/search.json?q={query}&limit=5").json()
            for item in r.get("docs", []):
                langs = item.get("language", [])
                lang_str = ", ".join(langs[:3]) if langs else "Desconhecido"
                
                key = item.get("key", "")
                is_public = item.get("public_scan_b", False)
                publish_year = item.get("first_publish_year")
                year_str = str(publish_year) if publish_year else None
                
                # Simplificação: Tudo que não é explicitamente público é marcado como Requer Empréstimo
                if is_public:
                    status = " [bold green](Domínio Público ✓)[/bold green]"
                else:
                    status = " [bold yellow](Requer Empréstimo 🔑)[/bold yellow]"
                
                authors = item.get("author_name", [])
                author_name = authors[0] if authors else "Autor Desconhecido"
                
                cover_id = item.get("cover_i")
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None

                results.append(BookSearchResult(
                    source="OpenLibrary",
                    title=f"{item.get('title', '')}{status}",
                    author=author_name,
                    language=lang_str,
                    link=f"https://openlibrary.org{key}",
                    year=year_str,
                    cover_url=cover_url
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
                lang_str = ", ".join(langs[:3]) if langs else "Desconhecido"
                
                key = item.get("key", "")
                is_public = item.get("public_scan_b", False)
                publish_year = item.get("first_publish_year")
                year_str = str(publish_year) if publish_year else None
                
                if is_public:
                    status = " [bold green](Domínio Público ✓)[/bold green]"
                else:
                    status = " [bold yellow](Requer Empréstimo 🔑)[/bold yellow]"
                
                authors = item.get("author_name", [])
                author_name = authors[0] if authors else "Autor Desconhecido"

                cover_id = item.get("cover_i")
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None

                results.append(BookSearchResult(
                    source="OpenLibrary",
                    title=f"{item.get('title', '')}{status}",
                    author=author_name,
                    language=lang_str,
                    link=f"https://openlibrary.org{key}",
                    year=year_str,
                    cover_url=cover_url
                ))
        except Exception:
            pass
        return results

    def can_download(self, url: str) -> bool:
        return "openlibrary.org/works/" in url or "openlibrary.org/books/" in url

    def _extract_olid(self, url: str) -> str:
        """Extrai o OLID (Ex: OL3422516W ou OL2591147M) da URL usando regex."""
        import re
        match = re.search(r'/(OL\d+[WM])', url)
        return match.group(1) if match else None

    def download(self, url: str, destiny_path: str) -> bool:
        """
        Tenta baixar o texto do Open Library. 
        Varre edições caso seja uma obra (work) para encontrar uma versão livre.
        """
        from src.application.interfaces import RestrictedBookError
        olid = self._extract_olid(url)
        if not olid:
            print(f"Erro: Não foi possível identificar o ID do OpenLibrary na URL.")
            return False

        try:
            # 1. Coletar IDs do Internet Archive (ia_ids)
            ia_ids = []
            
            obj_type = "works" if olid.endswith("W") else "books"
            
            # Tenta via Search primeiro (geralmente tem o ia_id principal)
            search_api = f"https://openlibrary.org/search.json?q=key:/{obj_type}/{olid}"
            r_search = requests.get(search_api).json()
            docs = r_search.get("docs", [])
            if docs:
                ia_ids.extend(docs[0].get("ia", []))
            
            # Se não achou ou se for uma 'work', vamos buscar nas edições explicitamente
            if obj_type == "works":
                editions_api = f"https://openlibrary.org/works/{olid}/editions.json?limit=50"
                r_editions = requests.get(editions_api).json()
                for entry in r_editions.get("entries", []):
                    if "ia" in entry:
                        ia_ids.extend(entry["ia"])
                    elif "ocaid" in entry:
                        ia_ids.append(entry["ocaid"])

            # Remove duplicatas mantendo a ordem
            ia_ids = list(dict.fromkeys(ia_ids))
            
            if not ia_ids:
                print(f"Aviso: Não foram encontrados registros digitais para '{olid}' ou suas edições.")
                return False

            # 2. Tentar download para cada ia_id encontrado
            tried_restricted = False
            
            for ia_id in ia_ids:
                possible_urls = [
                    f"https://archive.org/download/{ia_id}/{ia_id}_djvu.txt",
                    f"https://archive.org/download/{ia_id}/{ia_id}.txt",
                    f"https://archive.org/stream/{ia_id}/{ia_id}_djvu.txt"
                ]

                for d_url in possible_urls:
                    try:
                        resp = requests.get(d_url, timeout=10)
                        if resp.status_code == 200 and len(resp.text) > 1000:
                            if "<!DOCTYPE html>" in resp.text[:200]:
                                continue
                            with open(destiny_path, "w", encoding="utf-8") as f:
                                f.write(resp.text)
                            return True
                        elif resp.status_code in [401, 403]:
                            tried_restricted = True
                    except Exception:
                        continue

            # 3. Se falhou e detectamos restrição, lança o erro especializado
            if tried_restricted:
                 info = self.get_info(url)
                 raise RestrictedBookError(f"O livro '{olid}' requer empréstimo.", info=info)
            else:
                 print(f"Erro: Não foi possível encontrar um arquivo de texto livre para '{olid}'.")

        except RestrictedBookError:
            raise # Repassa o erro especializado
        except Exception as e:
            print(f"Erro ao processar OpenLibrary ({olid}): {e}")
            
        return False

    def get_info(self, url: str) -> BookSearchResult:
        try:
            olid = self._extract_olid(url)
            obj_type = "works" if olid.endswith("W") else "books"
            api_url = f"https://openlibrary.org/{obj_type}/{olid}.json"
            
            r = requests.get(api_url).json()
            title = r.get("title", "Título Desconhecido")
            
            # Tentar pegar idioma da API de busca para ser mais completo se for restricted display
            search_api = f"https://openlibrary.org/search.json?q=key:/{obj_type}/{olid}"
            r_s = requests.get(search_api).json()
            lang_str = "Desconhecido"
            year_str = None
            if r_s.get("docs"):
                doc = r_s["docs"][0]
                langs = doc.get("language", [])
                lang_str = ", ".join(langs[:3]) if langs else "Desconhecido"
                publish_year = doc.get("first_publish_year")
                year_str = str(publish_year) if publish_year else None

            # Tentar pegar autor
            author_name = "Autor Desconhecido"
            if r.get("authors"):
                author_key = r["authors"][0].get("author", {}).get("key")
                if author_key:
                    author_r = requests.get(f"https://openlibrary.org{author_key}.json").json()
                    author_name = author_r.get("name", "Autor Desconhecido")

            cover_id = r.get("covers", [None])[0]
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None
            
            if not cover_url and r_s.get("docs"):
                cover_id_s = r_s["docs"][0].get("cover_i")
                if cover_id_s:
                    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id_s}-M.jpg"

            return BookSearchResult(
                source="OpenLibrary",
                title=title,
                author=author_name,
                language=lang_str, 
                link=url,
                year=year_str,
                cover_url=cover_url
            )
        except Exception:
            return None
