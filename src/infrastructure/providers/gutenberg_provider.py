import sys
import os
import requests
import re
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.domain.entities import BookSearchResult
from src.application.interfaces import BookSearchProvider, BookDownloadProvider

class GutenbergProvider(BookSearchProvider, BookDownloadProvider):
    def search(self, query: str) -> List[BookSearchResult]:
        results = []
        try:
            r = requests.get(f"https://gutendex.com/books/?search={query}").json()
            for item in r.get("results", [])[:5]:
                langs = item.get("languages", [])
                if not langs:
                    continue
                lang_str = ", ".join(langs)
                book_id = item["id"]
                
                # Traduz do JSON para a nossa Entidade de Domínio Pura
                results.append(BookSearchResult(
                    source="Project Gutenberg",
                    title=item["title"],
                    language=lang_str,
                    link=f"https://www.gutenberg.org/ebooks/{book_id}"
                ))
        except Exception:
            pass
        return results

    def search_by_author(self, author: str) -> List[BookSearchResult]:
        """Gutendex API lida nativamente com buscas por autor através do parâmetro search principal."""
        return self.search(author)

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
            f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
            f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt"
        ]

        headers = {'User-Agent': 'MeuLeitorApp/1.0 (dev@exemplo.com)'}

        for txt_url in possiveis_urls:
            try:
                print(f"Tentando baixar {txt_url}...")
                r = requests.get(txt_url, headers=headers)
                if r.status_code == 200:
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
                return BookSearchResult(
                    source="Project Gutenberg",
                    title=r["title"],
                    language=lang_str,
                    link=url
                )
        except Exception:
            pass
        return None
