
import re
import os
import json
from typing import List, Dict, Optional

class BookAnalyzer:
    PATTERNS = [
        r'CAPÍTULO\s+[IVXLCDM\d]+',
        r'CHAPTER\s+[IVXLCDM\d]+',
        r'CANTO\s+[IVXLCDM\d]+',
        r'BOOK\s+[IVXLCDM\d]+',
        r'VOLUME\s+[IVXLCDM\d]+',
        r'PARTE\s+[IVXLCDM\d]+',
        r'PART\s+[IVXLCDM\d]+',
        r'PREFACE',
        r'PREFÁCIO',
        r'CONTENTS',
        r'ÍNDICE',
        r'INTRODUCTION',
        r'INTRODUÇÃO',
        r'FOOTNOTES',
        r'CENA\s+[IVXLCDM\d]+'
    ]

    def get_toc(self, filepath: str) -> List[str]:
        if not os.path.exists(filepath):
            return []
            
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = [f.readline() for _ in range(3000)]
            
        potential_headers = []
        # Pattern genérico para capturar qualquer coisa que pareça título
        combined_pattern = r'^\s*(' + '|'.join(self.PATTERNS) + r')(.*)$'
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped: continue
            if re.match(combined_pattern, stripped, re.IGNORECASE):
                potential_headers.append({'line': i, 'title': stripped})
        
        clusters = []
        current_cluster = []
        for i in range(len(potential_headers)):
            curr = potential_headers[i]
            if not current_cluster:
                current_cluster = [curr]
                continue
            
            prev = potential_headers[i-1]
            if curr['line'] - prev['line'] < 10:
                current_cluster.append(curr)
            else:
                if len(current_cluster) >= 3:
                    clusters.append(current_cluster)
                current_cluster = [curr]
        
        if len(current_cluster) >= 3:
            clusters.append(current_cluster)
            
        if not clusters:
            return []
            
        return [item['title'] for item in clusters[0]]

    def extract_chapter(self, filepath: str, toc: List[str], target_index: int) -> Dict:
        if target_index < 0 or target_index >= len(toc):
            return {"error": "Índice do Sumário inválido"}
            
        # Limpamos o título do TOC para busca (removemos pontos e espaços extras)
        def clean_title(t):
            t = re.sub(r'[\.\:]', '', t) # Remove pontos e dois pontos
            return t.strip().lower()

        target_clean = clean_title(toc[target_index])
        next_clean = clean_title(toc[target_index + 1]) if target_index + 1 < len(toc) else None
        
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # Encontrar a linha de início real (fora do sumário)
        real_start_line = -1
        
        # Procuramos o título no livro (usando regex para ignorar variações sutis)
        # ^\s*TITLE[\.\s]*$
        pattern_str = r'^\s*' + re.escape(target_clean).replace(r'\ ', r'\s+') + r'[\.\s]*$'
        
        for i, line in enumerate(lines):
            if i < 150: continue # Pula o provável bloco do sumário
            if re.match(pattern_str, line.strip().lower(), re.IGNORECASE):
                real_start_line = i
                break
        
        # Se não achou com match exato de linha, tenta em qualquer lugar da linha (para títulos longos)
        if real_start_line == -1:
            for i, line in enumerate(lines):
                if i < 150: continue
                if target_clean in clean_title(line):
                    real_start_line = i
                    break

        if real_start_line == -1:
            return {"error": f"Não localizei o início de '{toc[target_index]}'"}

        # Encontrar o fim (âncora do próximo título)
        real_end_line = len(lines)
        if next_clean:
            next_pattern = r'^\s*' + re.escape(next_clean).replace(r'\ ', r'\s+') + r'[\.\s]*$'
            for j in range(real_start_line + 1, len(lines)):
                if re.match(next_pattern, lines[j].strip().lower(), re.IGNORECASE):
                    real_end_line = j
                    break
                # Fallback se o próximo for parte de uma linha maior
                if next_clean in clean_title(lines[j]):
                    real_end_line = j
                    break

        content_lines = lines[real_start_line+1 : real_end_line]
        text_content = "".join(content_lines).strip()
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text_content) if p.strip()]
        
        return {
            "title": toc[target_index],
            "paragraphs": paragraphs
        }

if __name__ == "__main__":
    analyzer = BookAnalyzer()
    path = "/home/gangplank/projects/bibliocli/ebooks/Dante Alighieri/The Divine Comedy.txt"
    
    print(f"LIVRO: {os.path.basename(path)}")
    toc = analyzer.get_toc(path)
    
    # Usuário quer o capítulo 4 (BOOK IV)
    # Na Odisseia, BOOK IV costuma estar no índice 6 (0:Contents, 1:Preface, 2:Preface, 3:Odyssey, 4:Book I, 5:Book II, 6:Book III, 7:Book IV)
    # A saída anterior mostrou BOOK IV no índice 6.
    
    target_idx = 3 # BOOK IV
    if len(toc) > target_idx:
        print(f"\nExtraindo índice {target_idx}: {toc[target_idx]}")
        res = analyzer.extract_chapter(path, toc, target_idx)
        if "error" in res:
            print(f"Erro: {res['error']}")
        else:
            print(f"Sucesso! {len(res['paragraphs'])} parágrafos encontrados.")
            print("\nInício do Capítulo:")
            print(res['paragraphs'][0][:250] + "...")
