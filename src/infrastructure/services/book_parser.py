
import re
from typing import List, Set, Dict
from src.domain.models.book_models import Chapter

class BookParser:
    """
    Serviço especializado em analisar a estrutura de um livro (e-book).
    Usa uma abordagem de dois passos baseada no Sumário (TOC).
    """
    
    PATTERNS = [
        r'BOOK\s+[IVXLCDM\d]+',
        r'VOLUME\s+[IVXLCDM\d]+',
        r'PART\s+[IVXLCDM\d]+',
        r'PARTE\s+[IVXLCDM\d]+',
        r'CHAPTER\s+[IVXLCDM\d]+',
        r'CAPÍTULO\s+[IVXLCDM\d]+',
        r'CANTO\s+[IVXLCDM\d]+',
        r'LETTER\s+[IVXLCDM\d]+',
        r'CARTA\s+[IVXLCDM\d]+',
        r'ACT\s+[IVXLCDM\d]+',
        r'ATO\s+[IVXLCDM\d]+',
        r'SCENE\s+[IVXLCDM\d]+',
        r'SCENA\s+[IVXLCDM\d]+',
        r'HELL',
        r'PURGATORY',
        r'PARADISE',
        r'INFERNO',
        r'PURGATORIO',
        r'PARADISO',
        r'PREFACE',
        r'PREFÁCIO',
        r'INTRODUCTION',
        r'INTRODUÇÃO',
        r'CONTENTS',
        r'ÍNDICE',
        r'FOOTNOTES',
        r'CENA\s+[IVXLCDM\d]+'
    ]

    BAD_KEYWORDS = [
        'índice', 'index', 'contents', 'preface', 'prefácio', 'illustration', 
        'ilustración', 'dedicatória', 'title page', 'folha de rosto', 
        'copyright', 'license', 'footnotes', 'notas de rodapé', 'al professore',
        'foreword', 'prologue', 'prólogo', 'introduction', 'introdução'
    ]

    def _roman_to_int(self, s: str) -> int:
        """Converte uma string de caracteres romanos para int."""
        roman = {'i':1,'v':5,'x':10,'l':50,'c':100,'d':500,'m':1000}
        res = 0
        s = s.lower()
        try:
            for i in range(len(s)):
                if i > 0 and roman[s[i]] > roman[s[i-1]]:
                    res += roman[s[i]] - 2 * roman[s[i-1]]
                else:
                    res += roman[s[i]]
            return res
        except:
            return 0

    def _clean_title(self, title: str) -> str:
        """
        Limpa o título para facilitar a comparação.
        Normaliza romanos para arábicos (ex: CANTO II -> canto 2).
        """
        # Remove pontuação básica e hífens
        t = re.sub(r'[\.\:\-\–\—]', ' ', title)
        # Lowercase e trim
        t = t.strip().lower()
        
        # Normalização de algarismos romanos para arábicos
        # Procura por números romanos isolados (I, II, IV, etc)
        def replace_roman(match):
            roman_str = match.group(0)
            if len(roman_str) > 10: return roman_str # Segurança contra strings longas
            val = self._roman_to_int(roman_str)
            return str(val) if val > 0 else roman_str

        # Match apenas de caracteres romanos válidos
        t = re.sub(r'\b(?=[mdclxvi]+\b)m{0,4}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\b', replace_roman, t)
        
        # Remove espaços extras gerados
        return " ".join(t.split())

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Divide o texto em parágrafos baseados em linhas vazias."""
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def get_raw_headers(self, lines: List[str], max_lines: int = 100000) -> List[Dict]:
        """
        Descobre todos os candidatos a cabeçalhos nas primeiras X linhas.
        Usado para passar para a IA refinar e decidir o que é sumário real.
        """
        combined_pattern = r'^\s*(' + '|'.join(self.PATTERNS) + r')(.*)$'
        potential_headers = []
        
        limit = min(max_lines, len(lines))
        for i in range(limit):
            stripped = lines[i].strip()
            if not stripped: continue
            if re.match(combined_pattern, stripped, re.IGNORECASE):
                potential_headers.append({'line': i, 'title': stripped})
        
        return potential_headers

    def extract_chapter_content(self, full_text: str, chapter_title: str) -> str:
        """
        Dado o título de um capítulo, localiza-o no texto e retorna seu conteúdo
        até o próximo cabeçalho ou o fim do livro.
        """
        lines = full_text.split('\n')
        clean_target = self._clean_title(chapter_title)
        
        combined_pattern = r'^\s*(' + '|'.join(self.PATTERNS) + r')(.*)$'
        
        start_line = -1
        # 1. Localizar o início (precisamos pular o sumário)
        # Vamos assumir que se o título aparece mais de uma vez, 
        # a primeira é o sumário e a segunda é o início real.
        occurrences = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(combined_pattern, stripped, re.IGNORECASE):
                if self._clean_title(stripped) == clean_target:
                    occurrences.append(i)
        
        if not occurrences:
            return "Capítulo não encontrado."
            
        start_line = occurrences[-1] # Pega a última ocorrência (fora do sumário)
        
        # 2. Ler até o próximo cabeçalho qualquer
        content_lines = []
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if re.match(combined_pattern, line.strip(), re.IGNORECASE):
                break
            content_lines.append(line)
            
        return "\n".join(content_lines).strip()

    def find_toc_segments(self, lines: List[str]) -> List[Dict]:
        """
        Localiza os segmentos do arquivo que têm alta probabilidade de serem o sumário.
        Retorna uma lista de dicts com {'start': int, 'end': int, 'score': int, 'text': str}.
        """
        combined_pattern = r'^\s*(' + '|'.join(self.PATTERNS) + r')(.*)$'
        potential_headers = []
        
        # Analisa o início e o fim do livro (onde costumam estar os índices)
        check_ranges = [
            (0, min(4000, len(lines))), # Cabeça
            (max(0, len(lines)-2000), len(lines)) # Cauda
        ]
        
        seen_indices = set()
        for start, end in check_ranges:
            for i in range(start, end):
                if i in seen_indices: continue
                stripped = lines[i].strip()
                if not stripped: continue
                if re.match(combined_pattern, stripped, re.IGNORECASE):
                    potential_headers.append({'line': i, 'title': stripped})
                    seen_indices.add(i)

        clusters = []
        current_cluster = []
        
        # Agrupa headers próximos (distância < 4 linhas)
        # TOCs reais costumam ser muito densos. Um capítulo real dificilmente 
        # começa em menos de 4 linhas do seu título.
        for i in range(len(potential_headers)):
            curr = potential_headers[i]
            if not current_cluster:
                current_cluster = [curr]
                continue
            
            prev = potential_headers[i-1]
            if curr['line'] - prev['line'] < 4:
                current_cluster.append(curr)
            else:
                if len(current_cluster) >= 3:
                    clusters.append(current_cluster)
                current_cluster = [curr]
        
        if len(current_cluster) >= 3:
            clusters.append(current_cluster)

        # Transforma clusters em segmentos de texto
        segments = []
        for cluster in clusters:
            start_line = max(0, cluster[0]['line'] - 2)
            end_line = cluster[-1]['line'] + 1 # Fim exato após o último título do sumário
            
            # Tenta encontrar um marcador de início de sumário (ex: "CONTENTS")
            for j in range(cluster[0]['line'], max(0, cluster[0]['line'] - 20), -1):
                if re.search(r'^\s*(CONTENTS|INDEX|ÍNDICE|SUMÁRIO|INDEXO|CONTENTS)\s*$', lines[j], re.IGNORECASE):
                    start_line = j
                    break

            segment_text = "\n".join(lines[start_line:end_line+1])
            segments.append({
                'start': start_line,
                'end': end_line,
                'score': len(cluster),
                'text': segment_text,
                'headers': cluster
            })

        # Ordena pelo score (densidade de títulos)
        segments.sort(key=lambda x: x['score'], reverse=True)
        return segments

    def extract_toc_titles(self, lines: List[str]) -> (Set[str], int):
        """
        Versão legada/fallback da extração de sumário por heurística pura.
        """
        segments = self.find_toc_segments(lines)
        if not segments:
            return set(), 0
        
        best = segments[0]
        trusted_titles = set(self._clean_title(h['title']) for h in best['headers'])
        return trusted_titles, best['end']

    def parse_chapters(self, text: str, trusted_titles: Set[str] = None, toc_end_line: int = None) -> List[Chapter]:
        """
        Passo 2: Usa as âncoras do sumário para extrair os capítulos reais.
        """
        lines = text.split('\n')
        if trusted_titles is None or toc_end_line is None:
            trusted_titles, toc_end_line = self.extract_toc_titles(lines)
        
        combined_pattern = r'^\s*(' + '|'.join(self.PATTERNS) + r')(.*)$'
        valid_header_indices = []
        
        # 1. Mapear todas as âncoras reais
        for i, line in enumerate(lines):
            if i < toc_end_line: continue
            stripped = line.strip()
            if not stripped: continue
            
            if re.match(combined_pattern, stripped, re.IGNORECASE):
                clean_h = self._clean_title(stripped)
                if clean_h in trusted_titles:
                    valid_header_indices.append(i)

        # 2. Agrupamento em capítulos com detecção de ruído (TOC residual)
        chapters_data = []
        current_section = ""
        
        # Adicionamos um índice final fake para processar o último bloco
        indices_to_process = valid_header_indices + [len(lines)]
        
        for idx_ptr in range(len(indices_to_process) - 1):
            start_idx = indices_to_process[idx_ptr]
            end_idx = indices_to_process[idx_ptr + 1]
            
            title = lines[start_idx].strip()
            content_lines = lines[start_idx+1:end_idx]
            content = "\n".join(content_lines).strip()
            paras = self._split_into_paragraphs(content)
            
            # Heurística: se tem muitos parágrafos OU muito texto acumulado, é narrativa
            # Útil para poesias que podem ter poucos parágrafos mas são capítulos reais
            char_count = len(content)
            word_count = sum(len(p.split()) for p in paras)
            is_narrative = (len(paras) > 2 and word_count > 60) or (char_count > 500)
            
            # Se não for narrativa, pode ser uma Seção (HELL, PURGATORY)
            if not is_narrative:
                if len(title) < 60 and title.upper() == title:
                    current_section = title
                continue
            
            # Se for narrativa, aplicamos o prefixo da seção se existir
            final_title = title
            if current_section and current_section.lower() not in title.lower():
                final_title = f"{current_section} - {title}"
                
            chapters_data.append(Chapter(
                title=final_title,
                paragraphs=paras,
                is_narrative=True,
                index=len(chapters_data)
            ))

        # 3. Caso especial: se nenhum capítulo foi detectado (falha crítica), cria um único 'Livro Completo'
        if not chapters_data:
            narrative_text = "\n".join(lines[toc_end_line:])
            chapters_data.append(Chapter(
                title="Livro Completo",
                paragraphs=self._split_into_paragraphs(narrative_text),
                is_narrative=True,
                index=0
            ))

        return chapters_data
