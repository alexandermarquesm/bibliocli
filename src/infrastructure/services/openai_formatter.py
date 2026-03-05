
import os
import re
import json
from typing import List, Optional
from openai import OpenAI
from src.application.interfaces import BookTextFormatter
from src.domain.models.book_models import Chapter, FormattedBook
from src.infrastructure.services.book_parser import BookParser
from src.infrastructure.services.openai_toc_refiner import OpenAITocRefiner

class OpenAITextFormatter(BookTextFormatter):
    """
    Formatador de texto que combina limpeza bruta com uma estrutura de capítulos 
    detectada pelo BookParser e REFINADA por IA.
    """

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
        self.parser = BookParser()
        self.refiner = OpenAITocRefiner(api_key=self.api_key)

    def _apply_raw_cleaning_gutenberg(self, raw_text: str) -> str:
        """Remove headers e footers específicos do Project Gutenberg."""
        start_match = re.search(r'\*\*\* START OF [^\*]*\*\*\*', raw_text)
        end_match = re.search(r'\*\*\* END OF [^\*]*\*\*\*', raw_text)

        if start_match:
            raw_text = raw_text[start_match.end():]
        if end_match:
            raw_text = raw_text[:end_match.start()]
        
        return raw_text.strip()

    def format_text(self, raw_text: str, source: str = "gutenberg", title: str = None, author: str = None) -> str:
        """
        Ponto de entrada principal para formatar o livro.
        1. Limpa o texto bruto.
        2. Analisa a estrutura de capítulos via modular parser.
        3. Define o ponto de início sugerido.
        """
        # 1. Limpeza
        if source and "Gutenberg" in source:
            text = self._apply_raw_cleaning_gutenberg(raw_text)
        else:
            text = raw_text.strip()

        # 2. Parsing Modular da Estrutura (Raw)
        lines = text.split('\n')
        raw_headers = self.parser.get_raw_headers(lines)
        
        # 3. Refinamento por IA (O Cérebro)
        # Identifica segmentos prováveis de sumário para enviar apenas eles (Economia de Tokens)
        segments = self.parser.find_toc_segments(lines)
        toc_segment_text = segments[0]['text'] if segments else text[:3000] # Fallback se não detectar nada
        
        ai_toc = self.refiner.refine_toc(raw_headers, text[:3000])
        
        # 4. Extração Final de Capítulos
        # Se a IA retornou índices, usamos eles. Caso contrário, fallback heurístico.
        if ai_toc.get("toc_indices"):
            trusted_titles = set()
            for idx in ai_toc["toc_indices"]:
                if 0 <= idx < len(raw_headers):
                    title_raw = raw_headers[idx]['title']
                    trusted_titles.add(self.parser._clean_title(title_raw))
            
            toc_end_line = ai_toc.get("start_line", 0)
        else:
            trusted_titles, toc_end_line = self.parser.extract_toc_titles(lines)

        chapters = self.parser.parse_chapters(text, trusted_titles=trusted_titles, toc_end_line=toc_end_line)
        
        # 5. Lógica de Sugestão de Início (Suggest Start)
        suggested_start = {"chapter_index": 0, "paragraph_index": 0}
        
        # Tenta achar pelo índice do item que a IA identificou como início
        start_item_idx = ai_toc.get("start_item_index")
        if start_item_idx is not None and 0 <= start_item_idx < len(raw_headers):
            target_title = self.parser._clean_title(raw_headers[start_item_idx]['title'])
            for idx, ch in enumerate(chapters):
                if self.parser._clean_title(ch.title) == target_title:
                    suggested_start = {"chapter_index": idx, "paragraph_index": 0}
                    break
        
        book_data = FormattedBook(
            title=title or "Título Desconhecido",
            author=author or "Autor Desconhecido",
            chapters=chapters,
            suggested_start=suggested_start
        )

        return json.dumps(book_data.model_dump(), indent=2, ensure_ascii=False)
