from typing import Dict, Any
import json
from bibliocli.application.interfaces import BookTextFormatter

class GetBookMetadataUseCase:
    """
    Caso de Uso: Obter Sumário Refinado e Metadados do Livro.
    Coordena a análise inicial (cabeçalho) e retorna a estrutura inicial via dicionário.
    """
    def __init__(self, formatter: BookTextFormatter):
        self.formatter = formatter
        
    def execute(self, raw_text: str, title: str, author: str) -> Dict[str, Any]:
        """
        Gera a estrutura primária do livro delegando ao formatador, garantindo
        que retorne um dicionário acessível pelas camadas gordinhas do projeto.
        """
        formatted_json_string = self.formatter.format_text(raw_text, "generic_provider", title, author)
        
        try:
            return json.loads(formatted_json_string)
        except json.JSONDecodeError as e:
            # Torna o erro amigável na camada de Use Case antes de explodir para os controladores
            raise RuntimeError(f"O formatador falhou em retornar um JSON válido: {e}")
