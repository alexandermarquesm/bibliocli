import json
from typing import Optional, Any
from src.domain.models.book_models import FormattedBook
import hashlib

class BookRepository:
    """
    Interface Adapter: Repository for Persisting and Retrieving Formatted Books via Cloudflare KV.
    """
    def __init__(self, kv_binding: Any = None):
        self.kv = kv_binding

    def _get_key(self, author: str, title: str) -> str:
        author_safe = "".join([c for c in author if c.isalnum() or c in (' ', '-', '_')]).strip()
        title_safe = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
        return f"book:{author_safe}:{title_safe}".lower()

    def _get_url_key(self, url: str) -> str:
        # Usar um hash para a URL como chave para ser seguro e curto
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return f"url:{url_hash}"

    def save(self, book: FormattedBook) -> str:
        """Salva o livro formatado no Cloudflare KV."""
        if not self.kv:
            return "KV_NOT_CONFIGURED"

        from datetime import datetime
        book.updated_at = datetime.now().isoformat()
        
        data = json.dumps(book.model_dump(), ensure_ascii=False)
        
        # Salvar por Autor/Título
        key = self._get_key(book.author, book.title)
        self.kv.put(key, data)
        
        # Salvar por URL como índice
        url_key = self._get_url_key(book.source_url)
        self.kv.put(url_key, data)
        
        return key

    def find_formatted(self, author: str, title: str) -> Optional[dict]:
        """Busca um livro formatado no KV via Autor/Título."""
        if not self.kv:
            return None
            
        key = self._get_key(author, title)
        data = self.kv.get(key)
        if data:
            return json.loads(data)
        return None

    def find_by_url(self, url: str) -> Optional[dict]:
        """Busca um livro no KV através da URL de origem."""
        if not self.kv:
            return None
            
        url_key = self._get_url_key(url)
        data = self.kv.get(url_key)
        if data:
            return json.loads(data)
        return None
