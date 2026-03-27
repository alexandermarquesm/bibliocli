import json
import os
import libsql_client
from typing import Optional
from src.domain.models.book_models import FormattedBook

class TursoBookRepository:
    """
    Interface Adapter: Repository for Persisting and Retrieving Formatted Books via Turso (libsql).
    """
    def __init__(self):
        self.url = os.environ.get("TURSO_URL")
        self.auth_token = os.environ.get("TURSO_AUTH_TOKEN")
        
        if not self.url or not self.auth_token:
            self.client = None
            print("⚠️ [TURSO] Credentials missing. Turso repository will be disabled.")
        else:
            self.client = libsql_client.create_client(self.url, auth_token=self.auth_token)
            # A inicialização da tabela será feita via evento de startup do FastAPI

    def _ensure_table(self):
        if not self.client:
            return
        
        # We can't easily run async setup in __init__, so we rely on manual setup or first-run check
        # For simplicity in this serverless context, we expect the table to exist or we use a sync-like check if possible.
        # But libsql_client is primarily async.
        pass

    async def setup(self):
        if not self.client:
            return
        await self.client.execute("""
            CREATE TABLE IF NOT EXISTS formatted_books (
                url TEXT PRIMARY KEY,
                title TEXT,
                author TEXT,
                content TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    async def save(self, book: FormattedBook):
        """Salva o livro formatado no Turso."""
        if not self.client:
            return None
        
        data = json.dumps(book.model_dump(), ensure_ascii=False)
        await self.client.execute(
            "INSERT OR REPLACE INTO formatted_books (url, title, author, content) VALUES (?, ?, ?, ?)",
            (book.source_url, book.title, book.author, data)
        )
        return book.source_url

    async def find_by_url(self, url: str) -> Optional[dict]:
        """Busca um livro pela URL no Turso."""
        if not self.client:
            return None
        
        rs = await self.client.execute("SELECT content FROM formatted_books WHERE url = ?", (url,))
        if rs.rows:
            return json.loads(rs.rows[0][0])
        return None

    async def find_formatted(self, author: str, title: str) -> Optional[dict]:
        """Busca um livro pelo Autor e Título no Turso."""
        if not self.client:
            return None
        
        rs = await self.client.execute(
            "SELECT content FROM formatted_books WHERE author = ? AND title = ? LIMIT 1",
            (author, title)
        )
        if rs.rows:
            return json.loads(rs.rows[0][0])
        return None

    async def close(self):
        """Fecha a conexão com o Turso."""
        if self.client:
            await self.client.close()
            print("💤 [TURSO] Conexão fechada.")
