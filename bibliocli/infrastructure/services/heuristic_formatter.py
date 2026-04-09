import re
import json
from typing import List
from bibliocli.application.interfaces import BookTextFormatter
from bibliocli.domain.models.book_models import FormattedBook
from bibliocli.infrastructure.services.book_parser import BookParser

class HeuristicTextFormatter(BookTextFormatter):
    """
    Formatador Manual que extrai a estrutura de um texto confiando inteiramente em heurísticas (RegEx),
    operando sob a interface oficial BookTextFormatter para que seja intercambiável com IA.
    """
    def __init__(self):
        self.parser = BookParser()

    def _apply_raw_cleaning_gutenberg(self, raw_text: str) -> str:
        """Limpeza de cabecalhos/rodapes do Gutenberg."""
        start_match = re.search(r'\*\*\* START OF [^\*]*\*\*\*', raw_text)
        end_match = re.search(r'\*\*\* END OF [^\*]*\*\*\*', raw_text)

        if start_match:
            raw_text = raw_text[start_match.end():]
        if end_match:
            raw_text = raw_text[:end_match.start()]
        
        return raw_text.strip()

    def extract_toc_only(self, raw_text: str, source: str = "gutenberg") -> tuple:
        """
        Retorna (toc_end_line, structured_toc).
        Limpa espaços vazios, corta "Contents" e separa Prefixos de Capítulos de Títulos.
        """
        if source and "Gutenberg" in source.capitalize():
            text = self._apply_raw_cleaning_gutenberg(raw_text)
        else:
            text = raw_text.strip()
            
        lines = text.split('\n')
        segments = self.parser.find_toc_segments(lines)
        
        if not segments:
            return 0, []
            
        best_segment = segments[0]
        raw_toc_lines = best_segment['text'].split('\n')
        toc_end_line = best_segment['end']
        
        structured_toc = []
        
        # Padrão combinado do BookParser para extrair o prefixo (Ex: "CHAPTER I") do texto ("Down the Rabbit-Hole")
        combined_pattern = r'^\s*(' + '|'.join(self.parser.PATTERNS) + r')[\.\-\:]?\s+(.*)$'
        
        for line in raw_toc_lines:
            stripped_line = line.strip()
            
            # 1. Limpeza de Brancos
            if not stripped_line:
                continue
                
            # 2. Ignora o cabeçalho 'Contents' genérico puro
            if re.match(r'^(CONTENTS|SUMÁRIO|INDEX|ÍNDICE)\s*$', stripped_line, re.IGNORECASE):
                continue
                
            # 3. Tenta quebrar em Dict, se bater com um padrão reconhecido (Prefixo e Título)
            match = re.match(combined_pattern, stripped_line, re.IGNORECASE)
            if match:
                prefix = match.group(1).strip()
                title = match.group(2).strip()
                structured_toc.append({
                    "prefix": prefix,
                    "title": title
                })
            else:
                # Se for apenas um título solto, sem "CHAPTER X"
                structured_toc.append({
                    "prefix": "",
                    "title": stripped_line
                })
                
        return toc_end_line, structured_toc

    def _clean_chapter_paragraphs(self, paras: List[str]) -> List[str]:
        """Limpeza Final de Estética nos Parágrafos."""
        cleaned_paras = []
        asterisk_cluster_active = False
        
        for p in paras:
            # Verifica se o parágrafo inteiro é composto só por lixo decorativo (*      *      *)
            p_stripped_chars = p.replace(" ", "").replace("\n", "").replace("\r", "").replace("-", "")
            if p_stripped_chars and set(p_stripped_chars) == {'*'}:
                if not asterisk_cluster_active:
                    cleaned_paras.append("***") # Transforma um caos num único separador sútil
                    asterisk_cluster_active = True
            else:
                cleaned_paras.append(p)
                asterisk_cluster_active = False
                
        # 4. Remove um divisor de cena que foi capturado erroneamente no fim cego do capítulo
        if cleaned_paras and cleaned_paras[-1] == "***":
            cleaned_paras.pop()
            
        return cleaned_paras

    def _slice_chapters_from_toc(self, text: str, toc_data: list, toc_end_line: int) -> list:
        from bibliocli.domain.models.book_models import Chapter
        lines = text.split('\n')
        
        targets = []
        for item in toc_data:
            combined = (item['prefix'] + " " + item['title']).strip()
            targets.append(self.parser._clean_title(combined))
            
        valid_indices = []
        current_target_idx = 0
        
        if not targets:
            return []
            
        i = toc_end_line
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
                
            next_line = lines[i+1].strip() if i + 1 < len(lines) else ""
            
            clean_l = self.parser._clean_title(line)
            clean_combined = self.parser._clean_title(line + " " + next_line)
            
            matched = False
            # Busca janela de até 3 alvos a frente pra caso nós percamos um capítulo no OCR
            for step in range(min(3, len(targets) - current_target_idx)):
                candidate = targets[current_target_idx + step]
                if not candidate: continue
                # Match tolerante
                if candidate == clean_l or candidate == clean_combined or clean_l.startswith(candidate) or candidate.startswith(clean_l):
                    valid_indices.append((i, toc_data[current_target_idx + step]))
                    current_target_idx += step + 1
                    matched = True
                    break
                    
            if current_target_idx >= len(targets):
                break
                
            i += 1
            
        chapters = []
        if not valid_indices:
            return chapters # fallback
            
        # Adiciona um marcador final para sabermos onde acaba a varredura real
        valid_indices.append((len(lines), None))
        
        for idx in range(len(valid_indices) - 1):
            start, toc_ref = valid_indices[idx]
            end, _ = valid_indices[idx + 1]
            
            # 1. Compor Título Perfeito a partir do Sumário
            prefix = toc_ref.get("prefix", "")
            title_text = toc_ref.get("title", "")
            composed_title = f"{prefix} - {title_text}".strip(" - ") if prefix and title_text else prefix or title_text
            
            # 2. Impedir que o Título vá impresso repetido dentro do parágrafo
            # Adiantamos os ponteiros passados pelo Prefixo e Título se colidirem no começo do bloco
            content_start = start
            
            # Avançamos até no max 3 linhas para pular o prefix/title residual do texto
            lines_to_skip = 0
            for offset in range(0, min(3, end - start)):
                curr_line_clean = self.parser._clean_title(lines[start + offset])
                if not curr_line_clean: # Linha Vazia
                    lines_to_skip += 1
                elif curr_line_clean in self.parser._clean_title(prefix) or curr_line_clean in self.parser._clean_title(title_text):
                    lines_to_skip += 1
                else:
                    break
                    
            content_start += lines_to_skip
            
            content = "\n".join(lines[content_start:end]).strip()
            paras = self.parser._split_into_paragraphs(content)
            
            chapters.append(Chapter(
                title=composed_title,
                paragraphs=self._clean_chapter_paragraphs(paras),
                is_narrative=True,
                index=len(chapters)
            ))
            
        return chapters

    def format_text(self, raw_text: str, source: str = "gutenberg", title: str = None, author: str = None, only_toc: bool = False) -> str:
        # 1. Limpeza
        if source and "Gutenberg" in source.capitalize():
            text = self._apply_raw_cleaning_gutenberg(raw_text)
        else:
            text = raw_text.strip()
            
        # Extrai TOC limpinho
        toc_end_line, toc_data = self.extract_toc_only(raw_text, source)
        
        if only_toc:
            return json.dumps({"detected_toc": toc_data}, indent=2, ensure_ascii=False)
            
        # 2. Parsing usando o Crawler de Sumário
        chapters = []
        if len(toc_data) > 0 and toc_end_line > 0:
            chapters = self._slice_chapters_from_toc(text, toc_data, toc_end_line)
            
        # 3. Fallback (caso TOC tenha falhado ou nada capturado)
        if not chapters:
            chapters = self.parser.parse_chapters(text)
            # Aplicar limpeza nos parágrafos dos capítulos de fallback
            for ch in chapters:
                ch.paragraphs = self._clean_chapter_paragraphs(ch.paragraphs)
        
        book_data = FormattedBook(
            title=title or "Título Desconhecido",
            author=author or "Autor Desconhecido",
            chapters=chapters,
            suggested_start={"chapter_index": 0, "paragraph_index": 0} 
        )

        return json.dumps(book_data.model_dump(), indent=2, ensure_ascii=False)
