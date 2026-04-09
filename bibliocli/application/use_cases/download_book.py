import os
from typing import List, Tuple, Optional
from bibliocli.application.interfaces import BookDownloadProvider

class DownloadBookUseCase:
    """
    Coordena o 'Baixar um Livro'.
    Descobre qual provedor atende a URL inserida.
    """
    def __init__(self, providers: List[BookDownloadProvider]):
        self.providers = providers

    @staticmethod
    def _sanitize(text: str) -> str:
        """Limpa caracteres inseguros para criação de diretórios e arquivos."""
        if not text:
            return "unknown"
        return "".join([c for c in text if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
        
    def execute(self, url: str, destiny_dir: str, name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Gera a estrutura de pasta organizando por Autor e baixa o arquivo .txt lá.
        """
        for provider in self.providers:
            if provider.can_download(url):
                info = provider.get_info(url)
                
                final_name = name if name else (info.title if info else "livro_desconhecido")
                author_name = info.author if info else "Autor Desconhecido"
                
                safe_name = self._sanitize(final_name)
                safe_author = self._sanitize(author_name)
                
                if safe_name.lower().endswith(".txt"):
                    filename = safe_name
                else:
                    filename = f"{safe_name}.txt"
                
                author_dir = os.path.join(destiny_dir, safe_author)
                os.makedirs(author_dir, exist_ok=True)
                final_path = os.path.join(author_dir, filename)
                
                success = provider.download(url, final_path)
                return success, final_path if success else None
        
        return False, None
