import os
import json
import secrets
from typing import List, Tuple, Dict, Any, Optional

from bibliocli.application.interfaces import BookDownloadProvider, BookTextFormatter, IBookRepository
from bibliocli.domain.models.book_models import FormattedBook
from bibliocli.infrastructure.services.epub_formatter import EpubFormatter

class GetOrFormatBookUseCase:
    """
    Coordena inteiramente a lógica de obtenção e formatação primária de um e-book,
    seja via Banco de Dados (Cache Hit) ou via Download Inédito + Formatação via IA.
    
    Abstrai as tecnologias concretas (FileSystem, Turso, OpenAI) através das Interfaces passadas (DIP).
    """
    def __init__(
        self,
        providers: List[BookDownloadProvider],
        formatter: BookTextFormatter,
        repository: IBookRepository
    ):
        self.providers = providers
        self.formatter = formatter
        self.repository = repository

    async def execute(self, url: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        # 1. Encontrar o provedor qualificado
        provider = next((p for p in self.providers if getattr(p, 'can_download', None) and p.can_download(url)), None)
        
        if not provider:
             return None, "Nenhum provedor suporta o download desta URL."
             
        tmp_path = f"/tmp/bibliocli_temp_{secrets.token_hex(4)}.txt"

        try:
            book_info = provider.get_info(url)
            author = book_info.author if book_info else "Autor Desconhecido"
            title = book_info.title if book_info else "Título Desconhecido"
            
            # --- Tentar Hit de Cache ---
            formatted_data = await self.repository.find_by_url(url)
            
            if not formatted_data:
                formatted_data = await self.repository.find_formatted(author, title)

            if not formatted_data:
                # --- Miss de Cache: Baixar Cru e Usar Formatter Adequado ---
                success = provider.download(url, tmp_path)
                if not success:
                    return None, "Falha ao baixar do provedor."
                
                # Detectar se é EPUB (pelo cabeçalho do arquivo ZIP/EPUB)
                is_epub = False
                try:
                    with open(tmp_path, "rb") as f:
                        header = f.read(4)
                        if header == b"PK\x03\x04":
                            is_epub = True
                except Exception:
                    pass

                if is_epub:
                    formatter_to_use = EpubFormatter()
                    with open(tmp_path, "rb") as f:
                        raw_content = f.read()
                else:
                    formatter_to_use = self.formatter
                    with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                        raw_content = f.read()
                
                formatted_json_string = formatter_to_use.format_text(
                    raw_content, 
                    provider.__class__.__name__,
                    title=title,
                    author=author
                )
                
                # Transformar string da IA em um modelo seguro
                book_dict = json.loads(formatted_json_string)
                book_dict["source_url"] = url 
                book_obj = FormattedBook(**book_dict)
                
                # Salvar (A implementação dirá se salva no Turso ou Num FileSystem!)
                await self.repository.save(book_obj)
                
                formatted_data = book_obj.model_dump()
            
            result = {
                "book_url": url,
                "cover_url": getattr(book_info, 'cover_url', None) if book_info else None,
                "year": getattr(book_info, 'year', None) if book_info else None,
                "formatted_content": formatted_data
            }
            return result, None
            
        except Exception as e:
            return None, f"Erro inesperado no Workflow de Formatação: {str(e)}"
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
