import os
import sys
import json
import re
from typing import List, Set, Dict

# Adiciona a raiz do projeto ao path para encontrar o módulo 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.services.book_parser import BookParser
from src.infrastructure.services.openai_toc_refiner import OpenAITocRefiner
import requests
# Tenta ler o .env manualmente se existir
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("OPENAI_API_KEY="):
                val = line.split("=", 1)[1].strip().strip("'").strip('"')
                os.environ["OPENAI_API_KEY"] = val

# URL de teste da Divina Comédia (Longfellow translation)
DANTE_URL = "https://www.gutenberg.org/ebooks/8800.txt.utf-8"

def test_dante_summary():
    print("=== TESTE DE SUMÁRIO: DIVINA COMÉDIA ===")
    
    # 1. Obter texto bruto (simulando o download do Nexus)
    print(f"Buscando livro da URL: {DANTE_URL} ...")
    try:
        response = requests.get(DANTE_URL)
        if response.status_code != 200:
            print(f"Erro ao baixar o livro! Status code: {response.status_code}")
            return
        raw_text = response.text
    except Exception as e:
        print(f"Erro na requisição: {e}")
        return
    
    # 2. Inicializar Parser e Refiner
    parser = BookParser()
    refiner = OpenAITocRefiner()
    
    # 3. Extrair cabeçalhos brutos (Passo 1 do Pipeline)
    lines = raw_text.split('\n')
    raw_headers = parser.get_raw_headers(lines)
    print(f"Encontrados {len(raw_headers)} candidatos a cabeçalhos.")
    print("Primeiros 10 candidatos:")
    for h in raw_headers[:10]:
        print(f"  Linha {h['line']}: {h['title']}")
    
    # 4. Refinar com IA (Opcional, mas vamos fazer para testar o prompt novo)
    print("\nRefinando sumário com OpenAI GPT-4o-mini...")
    try:
        # Se você não preencheu OPENAI_API_KEY no terminal, isso pode falhar
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️ AVISO: OPENAI_API_KEY não encontrada no environment / .env")
            return

        try:
            # Passamos um preview das primeiras 5000 linhas para ajudar a IA a detectar o início
            preview = "\n".join(lines[:5000])
            refined_data = refiner.refine_toc(raw_headers, preview)
            
            toc_indices = refined_data.get("toc_indices", [])
            trusted_titles = set()
            for idx in toc_indices:
                if idx < len(raw_headers):
                    trusted_titles.add(parser._clean_title(raw_headers[idx]["title"]))
            
            start_line = refined_data.get("start_line", 0)
        except Exception as ai_e:
            print(f"⚠️ OpenAI indisponível ({ai_e}). Usando Fallback Heurístico...")
            segments = parser.find_toc_segments(lines)
            print(f"DEBUG: Segmentos encontrados pelo parser: {len(segments)}")
            for s in segments[:3]:
                 print(f"  Segmento: Linhas {s['start']}-{s['end']} (Score: {s['score']})")
                 
            trusted_titles, start_line = parser.extract_toc_titles(lines)
        
        print(f"\n✅ Linha de início detectada pela IA: {start_line}")
        print(f"✅ Títulos confiáveis (no sumário): {len(trusted_titles)}")
        
        # 5. Parsing Real de Capítulos (Passo 2 do Pipeline)
        print("\nProcessando capítulos estruturados...")
        # Note: start_line aqui serve como o toc_end_line para o parser
        chapters = parser.parse_chapters(raw_text, trusted_titles, start_line)
        
        print("\n=== RESUMO DO JSON QUE SERIA GERADO ===")
        print(f"Total de capítulos encontrados: {len(chapters)}")
        print("-" * 50)
        
        # Mostrar os primeiros 20 capítulos para verificação
        display_limit = 50
        count = 0
        for ch in chapters:
            is_narrative_icon = "📖" if ch.is_narrative else "📁"
            status = "TEXTO" if ch.is_narrative else "SEÇÃO/SUMÁRIO"
            print(f"{ch.index:3d}. {is_narrative_icon} [{status}] {ch.title}")
            count += 1
            if count >= display_limit:
                print(f"... e mais {len(chapters) - display_limit} capítulos.")
                break
                
        # Verificar se o Canto I do Hell está funcionando
        hell_canto_1 = next((ch for ch in chapters if "hell" in ch.title.lower() and "canto i" in ch.title.lower()), None)
        if hell_canto_1:
            print(f"\n✅ SUCESSO: Canto I de HELL encontrado!")
            print(f"   Título: {hell_canto_1.title}")
            print(f"   Preview: {hell_canto_1.paragraphs[0][:150]}...")
        else:
            print("\n❌ ERRO: Canto I de HELL não foi encontrado separadamente!")

    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dante_summary()
