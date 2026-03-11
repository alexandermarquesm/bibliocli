import sys
import os
import requests
import re
import json
import time
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.domain.entities import BookSearchResult
from src.application.interfaces import BookSearchProvider, BookDownloadProvider

class GutenbergProvider(BookSearchProvider, BookDownloadProvider):
    CACHE_FILE = os.path.expanduser("~/.bibliocli_cache/search_cache.json")
    CACHE_EXPIRATION = 86400  # 24 horas

    def _get_cache(self, key: str):
        if not os.path.exists(self.CACHE_FILE):
             return None
        try:
            with open(self.CACHE_FILE, "r") as f:
                cache_data = json.load(f)
            
            item = cache_data.get(key)
            if item:
                # Verificar expiração
                if time.time() - item["timestamp"] < self.CACHE_EXPIRATION:
                    # Reconstrói as entidades de domínio a partir do dict salvo
                    return [BookSearchResult(**b) for b in item["results"]]
                else:
                    # Limpar item expirado da memória (opcional, será sobrescrito)
                    pass
        except Exception:
            pass
        return None

    def _save_cache(self, key: str, results: List[BookSearchResult]):
        os.makedirs(os.path.dirname(self.CACHE_FILE), exist_ok=True)
        cache_data = {}
        if os.path.exists(self.CACHE_FILE):
             try:
                 with open(self.CACHE_FILE, "r") as f:
                     cache_data = json.load(f)
             except Exception:
                 pass
        
        # Converte as entidades para dict serializável
        cache_data[key] = {
            "timestamp": time.time(),
            "results": [vars(r) for r in results]
        }
        
        try:
             with open(self.CACHE_FILE, "w") as f:
                 json.dump(cache_data, f, ensure_ascii=False)
        except Exception:
             pass

    def search(self, query: str) -> List[BookSearchResult]:
        cache_key = f"search_{query}"
        cached = self._get_cache(cache_key)
        if cached is not None:
             return cached

        results = []
        try:
            # A API Gutendex costuma cair ou demorar, então o timeout de 10s é essencial
            r = requests.get(f"https://gutendex.com/books/?search={query}", timeout=10).json()
            for item in r.get("results", [])[:20]:
                langs = item.get("languages", [])
                if not langs:
                    continue
                lang_str = ", ".join(langs)
                book_id = item["id"]
                
                authors = item.get("authors", [])
                author_name = "Autor Desconhecido"
                year_proxy = None
                
                if authors:
                    author = authors[0]
                    name = author.get("name", "Autor Desconhecido")
                    
                    # Apenas o nome agora, conforme solicitado pelo usuário
                    author_name = name
                    
                    # O ano ainda é guardado no campo correto
                    death = author.get("death_year")
                    if death:
                        year_proxy = str(death)

                # Traduz do JSON para a nossa Entidade de Domínio Pura
                results.append(BookSearchResult(
                    source="Project Gutenberg",
                    title=item["title"],
                    author=author_name,
                    language=lang_str,
                    link=f"https://www.gutenberg.org/ebooks/{book_id}",
                    year=year_proxy,
                    cover_url=item.get("formats", {}).get("image/jpeg")
                ))
            
            # Salvar no cache apenas se tiver tido resposta completa
            self._save_cache(cache_key, results)
        except Exception as e:
            # Caso a API caia, retorna array vazio para a CLI tratar com civilidade
            pass
        return results

    def search_by_author(self, author: str) -> List[BookSearchResult]:
        """Gutendex API lida nativamente com buscas por autor através do parâmetro search principal."""
        return self.search(author)

    def get_popular_books(self) -> List[BookSearchResult]:
        """Gutendex retorna os mais populares por padrão se não houver query."""
        cache_key = "popular_books"
        cached = self._get_cache(cache_key)
        if cached is not None:
             return cached

        results = []
        try:
            r = requests.get("https://gutendex.com/books/", timeout=10).json()
            for item in r.get("results", [])[:20]:
                langs = item.get("languages", [])
                if not langs:
                    continue
                lang_str = ", ".join(langs)
                book_id = item["id"]
                
                authors = item.get("authors", [])
                author_name = "Autor Desconhecido"
                
                if authors:
                    author = authors[0]
                    author_name = author.get("name", "Autor Desconhecido")

                results.append(BookSearchResult(
                    source="Project Gutenberg",
                    title=item["title"],
                    author=author_name,
                    language=lang_str,
                    link=f"https://www.gutenberg.org/ebooks/{book_id}",
                    year=None,
                    cover_url=item.get("formats", {}).get("image/jpeg")
                ))
            self._save_cache(cache_key, results)
        except Exception:
            pass
        return results

    def can_download(self, url: str) -> bool:
        return "gutenberg.org/ebooks/" in url

    def download(self, url: str, destiny_path: str) -> bool:
        """
        Gutenberg expõe os seus e-books de graça. O ID fica no final do link.
        Ex: https://www.gutenberg.org/ebooks/1234
        Na maioria das vezes, o Txt limpo dele fica em:
        - https://www.gutenberg.org/cache/epub/1234/pg1234.txt.utf8 ou 
        - https://www.gutenberg.org/files/1234/1234-0.txt
        """
        match = re.search(r'ebooks/(\d+)', url)
        if not match:
            print("URL do Gutenberg inválida ou ID não encontrado.")
            return False
            
        book_id = match.group(1)
        
        possiveis_urls = [
            f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt.utf8",
            f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
            f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
            f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt"
        ]

        headers = {'User-Agent': 'MeuLeitorApp/1.0 (dev@exemplo.com)'}

        for txt_url in possiveis_urls:
            try:
                print(f"Tentando baixar {txt_url}...")
                r = requests.get(txt_url, headers=headers, timeout=10)
                if r.status_code == 200:
                    content_type = r.headers.get('Content-Type', '').lower()
                    if 'text/plain' not in content_type:
                        print(f"Aviso: URL {txt_url} retornou 200 mas o tipo é {content_type}, ignorando.")
                        continue

                    if len(r.content) < 1000: # Mínimo 1KB para um livro
                        print(f"Aviso: Arquivo baixado de {txt_url} parece muito pequeno ({len(r.content)} bytes).")
                        continue
                    with open(destiny_path, "wb") as f: # b para evitar bug de encoding na escrita 
                        f.write(r.content)
                    return True
            except Exception as e:
                print(f"Erro ao tentar link {txt_url}: {e}")

        print("Não foi possível encontrar uma versão TXT válida para essa ID do Gutenberg.")
        return False

    def get_info(self, url: str) -> BookSearchResult:
        match = re.search(r'ebooks/(\d+)', url)
        if not match:
            return None
        
        book_id = match.group(1)
        try:
            r = requests.get(f"https://gutendex.com/books/{book_id}").json()
            if "title" in r:
                langs = r.get("languages", [])
                lang_str = ", ".join(langs) if langs else "desconhecido"
                authors = r.get("authors", [])
                author_name = "Autor Desconhecido"
                if authors:
                    author = authors[0]
                    author_name = author.get("name", "Autor Desconhecido")

                # Tentar pegar o ano real (Release Date) no RDF do Gutenberg
                year = None
                try:
                    rdf_url = f"https://www.gutenberg.org/ebooks/{book_id}.rdf"
                    rdf_r = requests.get(rdf_url, timeout=5)
                    if rdf_r.status_code == 200:
                        # Extrair o ano do campo <dcterms:issued>
                        match_issued = re.search(r'<dcterms:issued[^>]*>(\d{4})', rdf_r.text)
                        if match_issued:
                            year = match_issued.group(1)
                except Exception:
                    pass

                return BookSearchResult(
                    source="Project Gutenberg",
                    title=r["title"],
                    author=author_name,
                    language=lang_str,
                    link=url,
                    year=year,
                    cover_url=r.get("formats", {}).get("image/jpeg")
                )
        except Exception:
            pass
        return None
