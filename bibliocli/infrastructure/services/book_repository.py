import os
import json
from typing import Optional
from bibliocli.domain.models.book_models import FormattedBook

class BookRepository:
    """
    Interface Adapter: Repository for Persisting and Retrieving Formatted Books locally.
    """
    def __init__(self, base_path: str = "ebooks"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def _get_path(self, author: str, title: str) -> str:
        author_safe = "".join([c for c in author if c.isalnum() or c in (' ', '-', '_')]).strip()
        title_safe = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
        
        author_dir = os.path.join(self.base_path, author_safe)
        if not os.path.exists(author_dir):
            os.makedirs(author_dir)
            
        return os.path.join(author_dir, f"{title_safe}.json")

    def save(self, book: FormattedBook) -> str:
        """Salva o livro formatado em um arquivo JSON local."""
        from datetime import datetime
        book.updated_at = datetime.now().isoformat()
        
        path = self._get_path(book.author, book.title)
        
        # Usar model_dump de Pydantic V2 (ou compatível)
        data = book.model_dump()
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return path

    def find_formatted(self, author: str, title: str) -> Optional[dict]:
        """Busca um livro formatado no disco."""
        path = self._get_path(author, title)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def find_by_url(self, url: str) -> Optional[dict]:
        """
        Originalmente não havia busca por URL no sistema de arquivos.
        Mantemos o método para compatibilidade de interface, mas retornamos None.
        """
        return None
