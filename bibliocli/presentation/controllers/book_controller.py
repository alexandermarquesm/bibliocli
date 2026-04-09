from typing import List, Optional
from bibliocli.application.use_cases import SearchBooksUseCase, SearchBooksByAuthorUseCase, GetPopularBooksUseCase
from bibliocli.domain.value_objects import BookSource, BookLink

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

    def get_popular_books(self, provider_name: str = "all"):
        # 1. Filter Providers
        active_providers = self.providers
        if provider_name.lower() != "all":
            active_providers = [
                p for p in self.providers 
                if provider_name.lower() in p.__class__.__name__.lower()
            ]

        # 2. Select and Execute Use Case
        use_case = GetPopularBooksUseCase(providers=active_providers)
        domain_results = use_case.execute()

        # 3. Return Entities
        return domain_results

    async def get_formatted_book(self, url: str, formatting_agent, options: dict, repo_turso=None):
        """
        Coordinates the execution of formatting via GetOrFormatBookUseCase,
        handling only Presentation Logic (data projection).
        """
        if not repo_turso:
            from bibliocli.infrastructure.services.turso_repository import TursoBookRepository
            repo_turso = TursoBookRepository()

        from bibliocli.application.use_cases import GetOrFormatBookUseCase
        from bibliocli.application.interfaces import BookDownloadProvider
        
        download_providers = [p for p in self.providers if isinstance(p, BookDownloadProvider)]
        
        use_case = GetOrFormatBookUseCase(
            providers=download_providers,
            formatter=formatting_agent,
            repository=repo_turso
        )
        
        result, error_msg = await use_case.execute(url)
        if error_msg or not result:
            return None, error_msg
            
        formatted_data = result.get("formatted_content", {})
        
        # --- Lógica de Apresentação (View Model Projection) ---
        chapter_index = options.get("chapter_index")
        only_metadata = options.get("only_metadata", False)
        
        if only_metadata:
            for ch in formatted_data.get("chapters", []):
                ch["paragraphs"] = []
                
        elif chapter_index is not None:
            if 0 <= chapter_index < len(formatted_data.get("chapters", [])):
                ch = formatted_data["chapters"][chapter_index]
                formatted_data["chapters"] = [ch]
            else:
                return None, "Índice de capítulo fora do intervalo."
                
        return result, None


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
