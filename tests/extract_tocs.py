import os
import sys
import re

# Adiciona a raiz do projeto ao path para encontrar o módulo 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List
from src.infrastructure.services.book_parser import BookParser

# CONFIGURAÇÃO: Agora você pode colocar o nome como preferir.
# O sistema vai verificar se todas as palavras estão no caminho do arquivo.
# Exemplo: "Dante Divine" vai achar "ebooks/Dante Alighieri/The Divine Comedy.txt"
# BOOK_NAME_FILTER = "Dante Alighieri/The divine comedy"
# BOOK_NAME_FILTER = "Homer/The Odyssey Rendered into English prose for the use of those who cannot read the original"
BOOK_NAME_FILTER = "Melville Herman/Moby Dick"


def main():
    parser = BookParser()
    ebooks_dir = "ebooks"
    
    # Prioritiza argumento de sistema, senão usa a constante
    filter_str = sys.argv[1] if len(sys.argv) > 1 else BOOK_NAME_FILTER
    
    print(f"=== BUSCANDO SUMÁRIO PARA: '{filter_str}' ===\n")
    found_any = False
    
    # Preparamos os termos para busca (removendo espaços extras)
    clean_filter = filter_str.lower().strip()
    filter_terms = clean_filter.split()
    
    for root, dirs, files in os.walk(ebooks_dir):
        for file in files:
            if file.endswith(".txt"):
                # Caminho relativo começando de ebooks/
                full_rel_path = os.path.join(os.path.relpath(root, ebooks_dir), file)
                full_path_low = full_rel_path.lower()
                
                # Procura 1: Tenta o match da string inteira (melhor para caminhos com /)
                # Procura 2: Se não for match literal, tenta o match de todas as palavras separadas
                match = (clean_filter in full_path_low) or (filter_terms and all(t in full_path_low for t in filter_terms))
                
                if not match:
                    continue
                
                found_any = True
                print(f"LIVRO ENCONTRADO: {full_rel_path}")
                path = os.path.join(root, file)
                print("-" * 60)
                
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        full_content = f.read()
                        lines = full_content.split('\n')[:3000]
                        
                        toc_titles, toc_end_line = parser.extract_toc_titles(lines)
                        
                        if toc_titles:
                            # 1. Mostrar o sumário detectado
                            print("  SUMÁRIO DETECTADO:")
                            combined_pattern = r'^\s*(' + '|'.join(parser.PATTERNS) + r')(.*)$'
                            for i, line in enumerate(lines):
                                stripped = line.strip()
                                if not stripped: continue
                                if re.match(combined_pattern, stripped, re.IGNORECASE):
                                    clean = parser._clean_title(stripped)
                                    # Só mostramos como TOC se estiver dentro do range detectado
                                    if clean in toc_titles and i <= toc_end_line:
                                        print(f"    [TOC] {stripped}")
                            
                            # 2. Mostrar o "Ponto de Início" (Para saber se pulou o prefácio)
                            print(f"\n  (O Sumário termina na linha {toc_end_line})")
                            print("\n  PREVIEW DO INÍCIO DA LEITURA (Suggested Start):")
                            chapters = parser.parse_chapters(full_content)
                            
                            # Lógica idêntica ao formatador oficial
                            suggested = None
                            skip_words = parser.BAD_KEYWORDS + ['início', 'title', 'intro', 'prologue', 'prólogo']
                            for ch in chapters:
                                if ch.is_narrative and not any(k in ch.title.lower() for k in skip_words):
                                    suggested = ch
                                    break
                            
                            if suggested:
                                print(f"    Capítulo: {suggested.title}")
                                print(f"    Texto: {suggested.paragraphs[0][:300]}...")
                            else:
                                print("    (Não foi possível identificar um início narrativo claro)")
                        else:
                            print("  (Nenhum sumário denso detectado)")
                except Exception as e:
                    print(f"  Erro: {e}")
                print("\n" + "="*60 + "\n")
    
    if filter_str and not found_any:
        print(f"Nenhum livro encontrado com o filtro: '{filter_str}'")

if __name__ == "__main__":
    main()
