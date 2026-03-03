import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from typing import List
from src.application.interfaces import BookDownloadProvider

class DownloadBookUseCase:
    """
    Coordena o Caso de Uso principal: 'Baixar um Livro'.
    Recebe os provedores (Downloaders) via injeção de dependência e descobre qual deles pode baixar a URL.
    """
    def __init__(self, providers: List[BookDownloadProvider]):
        self.providers = providers
        
    def execute(self, url: str, destiny_dir: str, name: str = None) -> (bool, str):
        for provider in self.providers:
            if provider.can_download(url):
                info = provider.get_info(url)
                
                if not name:
                    name = info.title if info else "livro_desconhecido"
                
                author_name = info.author if info else "Autor Desconhecido"
                
                # Sanitiza nomes para diretórios e arquivos
                def sanitize(text):
                    return "".join([c for c in text if c.isalnum() or c in (' ', '.', '_', '-')]).strip()

                safe_name = sanitize(name)
                safe_author = sanitize(author_name)
                
                # Garante que não temos extensão duplicada se o usuário passou .txt
                if safe_name.lower().endswith(".txt"):
                    filename = safe_name
                else:
                    filename = f"{safe_name}.txt"
                
                # Cria diretório do autor
                author_dir = os.path.join(destiny_dir, safe_author)
                os.makedirs(author_dir, exist_ok=True)
                
                final_path = os.path.join(author_dir, filename)
                
                success = provider.download(url, final_path)
                return success, final_path
        
        return False, None
