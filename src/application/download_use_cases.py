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
                if not name:
                    info = provider.get_info(url)
                    name = info.title if info else "livro_desconhecido"
                
                # Sanitiza o nome para arquivo
                safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '.', '_')]).strip()
                final_path = os.path.join(destiny_dir, f"{safe_name}.txt")
                
                success = provider.download(url, final_path)
                return success, final_path
        
        return False, None
