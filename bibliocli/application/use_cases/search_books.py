import sys
import os
from typing import List

from bibliocli.domain.entities import BookSearchResult
from bibliocli.application.interfaces import BookSearchProvider, ProviderUnavailableError

class SearchBooksUseCase:
    """
    Coordena a Busca de Livros.
    Recebe provedores via injeção de dependência e agrega os resultados.
    Foi refatorado para ter supressão condicional de erros: falha se TODOS falharem.
    """
    def __init__(self, providers: List[BookSearchProvider]):
        self.providers = providers
        
    def execute(self, query: str) -> List[BookSearchResult]:
        combined_results = []
        failed_providers = []
        
        for provider in self.providers:
            try:
                combined_results.extend(provider.search(query))
            except ProviderUnavailableError as e:
                failed_providers.append(e)
            except Exception: # Outros erros inesperados silenciados por design
                pass
        
        # Se temos resultados OU se pelo menos um provedor passou
        if combined_results or (len(failed_providers) < len(self.providers)):
             return combined_results
             
        # Se todos falharam
        if failed_providers:
             if len(failed_providers) == 1:
                  raise failed_providers[0]
             
             names = ", ".join([p.provider_name for p in failed_providers if getattr(p, 'provider_name', None)])
             raise ProviderUnavailableError(
                  f"Todos os provedores de busca falharam: {names}",
                  provider_name="TODOS"
             )
