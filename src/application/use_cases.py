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
    """
    def __init__(self, providers: List[BookSearchProvider]):
        self.providers = providers
        
    def execute(self, query: str) -> List[BookSearchResult]:
        combined_results = []
        for provider in self.providers:
            combined_results.extend(provider.search(query))
        return combined_results

class SearchBooksByAuthorUseCase:
    """
    Coordena o Caso de Uso: 'Buscar Obras por Autor'.
    Recebe os provedores via injeção de dependência e agrega os resultados estritos ao autor.
    """
    def __init__(self, providers: List[BookSearchProvider]):
        self.providers = providers
        
    def execute(self, author: str) -> List[BookSearchResult]:
        combined_results = []
        for provider in self.providers:
            combined_results.extend(provider.search_by_author(author))
        return combined_results
