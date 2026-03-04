from typing import List, Optional
from src.application.use_cases import SearchBooksUseCase, SearchBooksByAuthorUseCase
from src.domain.value_objects import BookSource, BookLink

class BookController:
    """
    Interface Adapter: Controller.
    Assembles the concrete providers (repositories) with the Use Cases.
    Serves as a bridge between the delivery mechanism (Web/CLI) and the Application layer.
    """
    def __init__(self, providers):
        self.providers = providers

    def get_search_results(self, query: str, search_type: str = "book", provider_name: str = "all"):
        # 1. Filter Providers (Repository Assembly)
        active_providers = self.providers
        if provider_name.lower() != "all":
            active_providers = [
                p for p in self.providers 
                if provider_name.lower() in p.__class__.__name__.lower()
            ]

        # 2. Select and Execute Use Case
        if search_type == "author":
            use_case = SearchBooksByAuthorUseCase(providers=active_providers)
        else:
            use_case = SearchBooksUseCase(providers=active_providers)
        
        domain_results = use_case.execute(query)

        # 3. Return Entities (Presentation Logic)
        # The caller (Web or CLI) will handle specific formatting/DTO mapping.
        return domain_results

    def get_formatted_book(self, url: str, formatting_agent, options: dict):
        """
        Coordinates the download and AI formatting of a book.
        """
        # Note: In a deeper refactor, this logic would move to a 
        # dedicated UseCase that interacts with a Storage Port and Formatter Port.
        provider = next((p for p in self.providers if hasattr(p, 'can_download') and p.can_download(url)), None)
        
        if not provider:
             return None, "Nenhum provedor suporta o download desta URL."
             
        import secrets
        import os
        import json
        
        tmp_path = f"/tmp/bibliocli_temp_{secrets.token_hex(4)}.txt"
        
        try:
            success = provider.download(url, tmp_path)
            if not success:
                return None, "Falha ao baixar texto bruto do provedor."
                
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
                
            book_info = provider.get_info(url)
            
            formatted_json_string = formatting_agent.format_text(
                raw_text, 
                provider.__class__.__name__,
                title=book_info.title if book_info else "Título Desconhecido",
                author=book_info.author if book_info else "Autor Desconhecido"
            )
            
            formatted_data = json.loads(formatted_json_string)
            
            # Application Logic (Optimization)
            chapter_index = options.get("chapter_index")
            if "chapters" in formatted_data and chapter_index is not None:
                if 0 <= chapter_index < len(formatted_data["chapters"]):
                    formatted_data["chapters"] = [formatted_data["chapters"][chapter_index]]
                else:
                    return None, "Índice de capítulo fora do intervalo."
            
            return {
                "book_url": url,
                "formatted_content": formatted_data
            }, None
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def get_raw_book(self, url: str):
        """
        Coordinates the download of raw book content.
        """
        provider = next((p for p in self.providers if hasattr(p, 'can_download') and p.can_download(url)), None)
        
        if not provider:
             return None, None, "Nenhum provedor suporta o download desta URL."
        
        import secrets
        import os
        
        tmp_path = f"/tmp/raw_{secrets.token_hex(4)}.txt"
        try:
            success = provider.download(url, tmp_path)
            if not success:
                return None, None, "Falha ao baixar texto do provedor."
            
            book_info = provider.get_info(url)
            # Sanitizar nome do arquivo
            title_safe = "".join([c for c in book_info.title if c.isalnum() or c in (' ', '-', '_')]).strip()
            filename = f"{title_safe}.txt"

            with open(tmp_path, "rb") as f:
                content = f.read()

            return content, filename, None
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
