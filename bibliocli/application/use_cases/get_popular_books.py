import sys
import os
from typing import List

from bibliocli.domain.entities import BookSearchResult
from bibliocli.application.interfaces import BookSearchProvider, ProviderUnavailableError

class GetPopularBooksUseCase:
    """
    Obtém livros populares dos provedores ativos.
    """
    def __init__(self, providers: List[BookSearchProvider]):
        self.providers = providers
        
    def execute(self) -> List[BookSearchResult]:
        combined_results = []
        failed_providers = []
        
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
             names = ", ".join([p.provider_name for p in failed_providers if getattr(p, 'provider_name', None)])
             raise ProviderUnavailableError(
                  f"Todos os provedores de populares falharam: {names}",
                  provider_name="TODOS"
             )
