import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from typing import List
from src.domain.entities import BookSearchResult
from src.application.interfaces import BookSearchProvider

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
