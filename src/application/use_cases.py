import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from typing import List
from src.domain.entities import BookSearchResult
from src.application.interfaces import BookSearchProvider

from src.domain.models.book_models import Chapter, FormattedBook
from src.application.interfaces import BookSearchProvider, BookTextFormatter
from src.infrastructure.services.book_parser import BookParser

class GetBookMetadataUseCase:
    """
    Caso de Uso: Obter Sumário Refinado e Metadados do Livro.
    Coordena a análise inicial (cabeçalho) com o auxílio da IA.
    """
    def __init__(self, formatter: BookTextFormatter):
        self.formatter = formatter
        
    def execute(self, raw_text: str, title: str, author: str) -> dict:
        # A implementação atual do format_text já utiliza o IA Cleaner internamente
        # para retornar o objeto FormattedBook completo.
        formatted_json = self.formatter.format_text(raw_text, "gutenberg", title, author)
        from json import loads
        return loads(formatted_json)

class GetBookChapterUseCase:
    """
    Caso de Uso: Obter Conteúdo de um Capítulo Específico.
    Usa Heurísticas de slicing para não precisar processar o livro todo de novo.
    """
    def __init__(self, parser: BookParser):
        self.parser = parser
        
    def execute(self, full_text: str, chapter_title: str) -> str:
        return self.parser.extract_chapter_content(full_text, chapter_title)

class SearchBooksUseCase:
    """
    Coordena o Caso de Uso principal: 'Buscar Livros'.
    Recebe os provedores via injeção de dependência e agrega os resultados de Forma Limpa.
    Resiliência Inteligente: Suprime erros se houver resultados parciais, mas falha se todos caírem.
    """
    def __init__(self, providers: List[BookSearchProvider]):
        self.providers = providers
        
    def execute(self, query: str) -> List[BookSearchResult]:
        combined_results = []
        failed_providers = []
        from src.application.interfaces import ProviderUnavailableError
        
        for provider in self.providers:
            try:
                combined_results.extend(provider.search(query))
            except ProviderUnavailableError as e:
                failed_providers.append(e)
            except Exception: # Outros erros inesperados
                pass
        
        # Se temos resultados OU se pelo menos um provedor passou (mesmo sem livros)
        # nós silenciamos os erros parciais para não atrapalhar a UX global.
        if combined_results or (len(failed_providers) < len(self.providers)):
             return combined_results
             
        # Se chegou aqui, é porque TODOS os provedores falharam.
        if failed_providers:
             if len(failed_providers) == 1:
                  raise failed_providers[0]
             
             names = ", ".join([p.provider_name for p in failed_providers if p.provider_name])
             raise ProviderUnavailableError(
                  f"Todos os provedores de busca falharam: {names}",
                  provider_name="TODOS"
             )
             
        return combined_results

class SearchBooksByAuthorUseCase:
    """
    Coordena o Caso de Uso: 'Buscar Obras por Autor'.
    """
    def __init__(self, providers: List[BookSearchProvider]):
        self.providers = providers
        
    def execute(self, author: str) -> List[BookSearchResult]:
        combined_results = []
        failed_providers = []
        from src.application.interfaces import ProviderUnavailableError
        
        for provider in self.providers:
            try:
                combined_results.extend(provider.search_by_author(author))
            except ProviderUnavailableError as e:
                failed_providers.append(e)
            except Exception:
                pass
        
        if combined_results or (len(failed_providers) < len(self.providers)):
             return combined_results
             
        if failed_providers:
             if len(failed_providers) == 1:
                  raise failed_providers[0]
             names = ", ".join([p.provider_name for p in failed_providers if p.provider_name])
             raise ProviderUnavailableError(f"Todos os provedores falharam: {names}", provider_name="TODOS")
        return combined_results

class GetPopularBooksUseCase:
    """
    Coordena o Caso de Uso: 'Obter Livros Populares'.
    """
    def __init__(self, providers: List[BookSearchProvider]):
        self.providers = providers
        
    def execute(self) -> List[BookSearchResult]:
        combined_results = []
        failed_providers = []
        from src.application.interfaces import ProviderUnavailableError
        
        for provider in self.providers:
            try:
                combined_results.extend(provider.get_popular_books())
            except ProviderUnavailableError as e:
                failed_providers.append(e)
            except Exception:
                pass
        
        if combined_results or (len(failed_providers) < len(self.providers)):
             return combined_results
             
        if failed_providers:
             if len(failed_providers) == 1:
                  raise failed_providers[0]
             names = ", ".join([p.provider_name for p in failed_providers if p.provider_name])
             raise ProviderUnavailableError(f"Todos os provedores falharam: {names}", provider_name="TODOS")
        return combined_results
