import os
import json
from typing import Optional
from src.domain.models.book_models import FormattedBook

class BookRepository:
    """
    Interface Adapter: Repository for Persisting and Retrieving Formatted Books.
    Follows Clean Architecture by abstracting the filesystem details.
    """
    def __init__(self, base_path: str = "ebooks"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def _get_path(self, author: str, title: str) -> str:
        # Sanitizar nomes para pastas/arquivos
        author_safe = "".join([c for c in author if c.isalnum() or c in (' ', '-', '_')]).strip()
        title_safe = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
        
        folder = os.path.join(self.base_path, author_safe)
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        return os.path.join(folder, f"{title_safe}.json")

    def save(self, book: FormattedBook) -> str:
        """Salva o livro formatado como JSON no disco."""
        from datetime import datetime
        book.updated_at = datetime.now().isoformat()
        
        path = self._get_path(book.author, book.title)
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(book.model_dump(), indent=2, ensure_ascii=False))
        return path

    def find_formatted(self, author: str, title: str) -> Optional[dict]:
        """Busca um livro formatado no cache local."""
        path = self._get_path(author, title)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def find_by_url(self, url: str) -> Optional[dict]:
        """
        Busca um livro no cache local através da URL de origem.
        Isso é mais confiável que Author/Title, pois a URL é única.
        """
        # Caminha pela árvore ebooks/ em busca do JSON que contém a URL
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith(".json"):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if data.get("source_url") == url:
                                return data
                    except Exception:
                        continue
        return None
