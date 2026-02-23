from dataclasses import dataclass

@dataclass
class BookSearchResult:
    """
    Entidade de Domínio principal.
    Não conhece nada sobre bibliotecas externas como Requests ou Rich.
    Apenas reflete o modelo de dados puro que o nosso sistema entende por 'Resultado de Busca'.
    """
    source: str
    title: str
    language: str
    link: str
