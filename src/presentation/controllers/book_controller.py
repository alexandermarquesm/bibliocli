from typing import List, Optional
from src.application.use_cases import SearchBooksUseCase, SearchBooksByAuthorUseCase, GetPopularBooksUseCase
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
        Coordinates the download and AI formatting of a book.
        """
        provider = next((p for p in self.providers if hasattr(p, 'can_download') and p.can_download(url)), None)
        
        if not provider:
             return None, "Nenhum provedor suporta o download desta URL."
             
        import secrets
        import os
        import json
        
        # Se não foi passado um repositório (ex: CLI), cria um local
        if not repo_turso:
            from src.infrastructure.services.turso_repository import TursoBookRepository
            repo_turso = TursoBookRepository()
        
        tmp_path = f"/tmp/bibliocli_temp_{secrets.token_hex(4)}.txt"

        try:
            book_info = provider.get_info(url)
            author = book_info.author if book_info else "Autor Desconhecido"
            title = book_info.title if book_info else "Título Desconhecido"
            
            # --- Lógica de Cache (Turso) ---
            # Tentar carregar pelo Turso Primeiro (Nuvem Persistente)
            formatted_data = await repo_turso.find_by_url(url)
            if formatted_data:
                print(f"🌌 [CACHE TURSO] Livro encontrado via URL: {url}")
            
            if not formatted_data:
                # Tentar carregar pelo Autor/Título no Turso como fallback
                formatted_data = await repo_turso.find_formatted(author, title)
                if formatted_data:
                    print(f"🌌 [CACHE TURSO] Livro encontrado via Autor/Título: {author} - {title}")

            if not formatted_data:
                print(f"🌐 [NEW BOOK] Livro não encontrado no Turso. Iniciando Download e Processamento IA...")
                # Baixar e Formatar
                success = provider.download(url, tmp_path)
                if not success:
                    return None, "Falha ao baixar texto bruto do provedor."
                    
                with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()
                
                # Formatação Completa (incluindo IA)
                formatted_json_string = formatting_agent.format_text(
                    raw_text, 
                    provider.__class__.__name__,
                    title=title,
                    author=author
                )
                
                # Converter para Modelo Pydantic para validar e salvar
                from src.domain.models.book_models import FormattedBook
                book_dict = json.loads(formatted_json_string)
                book_dict["source_url"] = url 
                book_obj = FormattedBook(**book_dict)
                
                # Salvar no Turso
                try:
                    await repo_turso.save(book_obj)
                    print(f"💾 [SAVED TURSO] Livro salvo no banco de dados Turso.")
                except Exception as e:
                    print(f"⚠️ [TURSO ERROR] Falha ao salvar no Turso: {e}")
                
                formatted_data = book_obj.model_dump()
            
            from src.application.use_cases import GetBookMetadataUseCase, GetBookChapterUseCase
            from src.infrastructure.services.book_parser import BookParser
            
            # --- Lógica de Otimização (Lazy Loading para entrega API) ---
            chapter_index = options.get("chapter_index")
            only_metadata = options.get("only_metadata", False)
            
            # Nota: O texto bruto ainda é necessário para o chapter_uc se não tivermos parágrafos no JSON
            # Mas como o JSON mestre já tem tudo, podemos filtrar direto dele.
            
            if only_metadata:
                # Remove os parágrafos para não pesar a resposta da rede
                for ch in formatted_data.get("chapters", []):
                    ch["paragraphs"] = []
            
            elif chapter_index is not None:
                if 0 <= chapter_index < len(formatted_data["chapters"]):
                    ch = formatted_data["chapters"][chapter_index]
                    formatted_data["chapters"] = [ch]
                else:
                    return None, "Índice de capítulo fora do intervalo."
            
            return {
                "book_url": url,
                "cover_url": book_info.cover_url if book_info else None,
                "year": book_info.year if book_info else None,
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
