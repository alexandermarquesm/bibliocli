
import re
import json
from typing import List, Set, Dict
from openai import OpenAI
import os

class OpenAITocRefiner:
    """
    Serviço de Infraestrutura que utiliza o modelo GPT-4o-mini para limpar 
    listas de cabeçalhos brutos e identificar o Sumário Real.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def refine_toc(self, raw_headers: List[Dict], preview_text: str) -> Dict:
        """
        Envia os candidatos a cabeçalhos para a IA decidir quais são o sumário real.
        """
        if not self.client:
            return {"toc_indices": [], "start_line": 0}

        # Prepara a amostra com índices para a IA referenciar
        headers_sample = [f"#{i} (Linha {h['line']}): {h['title']}" for i, h in enumerate(raw_headers)]
        
        prompt = f"""
Você é um especialista em estruturação de livros clássicos.
Eu extraí candidatos a títulos de capítulos de um e-book bruto.

LISTA DE CANDIDATOS:
{chr(10).join(headers_sample)}

TAREFA:
1. Identifique quais itens (#índice) pertencem ao ÍNDICE/SUMÁRIO real de navegação.
2. Identifique qual item (#índice) marca o Primeiro Capítulo Real da narrativa onde o TEXTO DA HISTÓRIA começa.
3. Para livros como 'A Divina Comédia', ignore as listas de cantos que aparecem antes do texto real de cada parte.

REGRAS:
- 'start_line': Deve ser a linha exata onde o TEXTO do primeiro capítulo começa (logo após o título dele no corpo do livro).
  IMPORTANTE: Se houver uma lista de capítulos ("LIST OF CANTOS") antes do texto, ignore-a e aponte para o título real no corpo do livro.
- Retorne apenas os ÍNDICES numéricos da lista acima.

RETORNE APENAS JSON:
{{
  "toc_indices": [indices_dos_itens_no_sumario],
  "start_item_index": indice_do_primeiro_capitulo_real,
  "start_line": linha_onde_o_texto_desse_capitulo_comeca
}}
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Responda apenas com JSON plano."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
