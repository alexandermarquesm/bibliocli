import os
import re
import json
from typing import List, Optional
from pydantic import BaseModel
from openai import OpenAI
from src.application.interfaces import BookTextFormatter

class Chapter(BaseModel):
    title: str
    paragraphs: List[str]
    
class FormattedBook(BaseModel):
    title: str
    author: str
    chapters: List[Chapter]

class OpenAITextFormatter(BookTextFormatter):
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def _apply_raw_cleaning_gutenberg(self, raw_text: str) -> str:
        start_match = re.search(r'\*\*\* START OF [^\*]*\*\*\*', raw_text)
        end_match = re.search(r'\*\*\* END OF [^\*]*\*\*\*', raw_text)

        if start_match:
            start_idx = start_match.end()
            end_idx = end_match.start() if end_match else len(raw_text)
            return raw_text[start_idx:end_idx].strip()
        
        return raw_text.strip()

    def _split_into_paragraphs(self, text: str) -> List[str]:
        # Divide por uma ou mais linhas em branco
        paragraphs = re.split(r'\n\s*\n', text)
        # Limpa espaços e remove parágrafos vazios
        return [p.strip() for p in paragraphs if p.strip()]

    def _detect_chapters(self, text: str) -> List[Chapter]:
        """
        Heurística simples para detectar capítulos:
        Procure por 'CAPÍTULO', 'CHAPTER', 'CENA', ou números romanos sozinhos em uma linha.
        """
        # Padrões comuns de início de capítulo
        patterns = [
            r'^(CAPÍTULO\s+[IVXLCDM\d]+.*)$',
            r'^(CHAPTER\s+[IVXLCDM\d]+.*)$',
            r'^([IVXLCDM]{1,7}\.*)$', # Números romanos isolados
            r'^(CENA\s+[IVXLCDM\d]+.*)$'
        ]
        
        lines = text.split('\n')
        chapters_data = []
        current_chapter_title = "Início"
        current_chapter_lines = []

        for line in lines:
            stripped = line.strip()
            is_header = False
            for p in patterns:
                if re.match(p, stripped, re.IGNORECASE):
                    # Se temos conteúdo acumulado, salve o capítulo anterior
                    if current_chapter_lines:
                        content = "\n".join(current_chapter_lines)
                        chapters_data.append(Chapter(
                            title=current_chapter_title,
                            paragraphs=self._split_into_paragraphs(content)
                        ))
                    
                    current_chapter_title = stripped
                    current_chapter_lines = []
                    is_header = True
                    break
            
            if not is_header:
                current_chapter_lines.append(line)

        # Adiciona o último capítulo
        if current_chapter_lines:
            content = "\n".join(current_chapter_lines)
            chapters_data.append(Chapter(
                title=current_chapter_title,
                paragraphs=self._split_into_paragraphs(content)
            ))

        return chapters_data

    def format_text(self, raw_text: str, source: str, title: str = None, author: str = None) -> str:
        cleaned_text = raw_text
        
        # 1. Limpeza básica Regex (Gutenberg)
        if "gutenberg" in source.lower():
            cleaned_text = self._apply_raw_cleaning_gutenberg(raw_text)

        # 2. Uso Inteligente de IA (Apenas no início para remover prefácios e lixo)
        if self.client and len(cleaned_text) > 1000:
            try:
                # Enviar apenas os primeiros 15k caracteres para limpeza de cabeçalho
                head_limit = 15000
                head_chunk = cleaned_text[:head_limit]
                remaining_text = cleaned_text[head_limit:]
                
                prompt = (
                    "Você é um assistente especializado em limpar e-books para motores de Voz (TTS). "
                    "Vou te mandar o INÍCIO de um livro. Sua tarefa é remover TUDO o que não faz parte da história real. "
                    "Remova: Folhas de rosto, dedicatórias, índices, prefácios de tradutores e notas de copyright. "
                    "Mantenha APENAS o texto literário a partir de onde o livro realmente começa. "
                    "Retorne o texto limpo exatamente como escrito, sem comentários."
                )
                
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": head_chunk}
                    ],
                    temperature=0
                )
                
                llm_cleaned_head = response.choices[0].message.content.strip()
                cleaned_text = llm_cleaned_head + "\n\n" + remaining_text
            except Exception as e:
                print(f"Aviso: Erro na limpeza via IA, usando limpeza básica: {e}")

        # 3. Heurística de Capítulos e Parágrafos
        chapters = self._detect_chapters(cleaned_text)
        
        # Se não detectou nada, cria um capítulo único
        if not chapters:
            chapters = [Chapter(
                title="Conteúdo Completo",
                paragraphs=self._split_into_paragraphs(cleaned_text)
            )]

        return FormattedBook(
            title=title or "Título Desconhecido",
            author=author or "Autor Desconhecido",
            chapters=chapters
        ).model_dump_json()
