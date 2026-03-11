import sys
import os

# Adiciona ao sys.path para importações absolutas limpas (opcional num projeto uv configurado, mas prático guiado por script direto)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from abc import ABC, abstractmethod
from typing import List
from src.domain.entities import BookSearchResult

class RestrictedBookError(Exception):
    """Exceção lançada quando um livro exige login/empréstimo para ser baixado."""
    def __init__(self, message: str, info: BookSearchResult = None):
        super().__init__(message)
        self.info = info

class BookSearchProvider(ABC):
    """
    Interface/Contrato (Port) do que um Provedor de Busca deve fazer.
    A camada de Aplicação só conversa com isso, e a Infraestrutura é obrigada a implementá-la.
    """
    @abstractmethod
    def search(self, query: str) -> List[BookSearchResult]:
        pass

    @abstractmethod
    def search_by_author(self, author: str) -> List[BookSearchResult]:
        pass

    @abstractmethod
    def get_popular_books(self) -> List[BookSearchResult]:
        pass

class BookDownloadProvider(ABC):
    """
    Interface/Contrato (Port) para Provedores de Download.
    """
    @abstractmethod
    def can_download(self, url: str) -> bool:
        """Verifica se esse provedor é responsável pela URL recebida"""
        pass

    @abstractmethod
    def download(self, url: str, destiny_path: str) -> bool:
        """Baixa o conteúdo do livro para o disco e retorna True se teve sucesso"""
        pass

    @abstractmethod
    def get_info(self, url: str) -> BookSearchResult:
        """Busca informações básicas do livro (como título) a partir da URL"""
        pass
class BookTextFormatter(ABC):
    """
    Interface/Contrato para formatadores e limpadores de texto.
    Pode implementar limpeza via Regex, LLM ou heurísticas.
    """
    @abstractmethod
    def format_text(self, raw_text: str, source: str, title: str = None, author: str = None) -> str:
        """Retorna o texto (geralmente em formato JSON estruturado) pronto para consumo"""
        pass
