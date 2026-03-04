from dataclasses import dataclass
from typing import Optional
from .value_objects import BookSource, BookLink

@dataclass
class BookSearchResult:
    """
    Entidade de Domínio principal.
    Utiliza Value Objects para garantir integridade dos dados sem depender de frameworks.
    """
    source: BookSource
    title: str
    author: str
    language: str
    link: BookLink
    year: Optional[str] = None
