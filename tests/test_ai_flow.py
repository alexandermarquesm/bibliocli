
import sys
import os
import json

# Ajusta path para importar src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.services.openai_formatter import OpenAITextFormatter
from src.infrastructure.services.book_parser import BookParser
from src.application.use_cases import GetBookMetadataUseCase, GetBookChapterUseCase

def test_full_ai_flow():
    """
    Simula o fluxo real que o usuário pediu:
    1. IA analisa o sumário e remove ruídos.
    2. Usamos o sumário da IA para buscar um capítulo específico por nome.
    """
    print("\n--- TESTANDO FLUXO COMPLETO COM IA (CLEAN ARCHITECTURE) ---")
    
    # Configurações
    book_path = "ebooks/Melville Herman/Moby Dick.txt"
    if not os.path.exists(book_path):
        print(f"Erro: Livro não encontrado em {book_path}")
        return

    # 1. SETUP (Camada de Infra)
    formatter = OpenAITextFormatter()
    parser = BookParser()
    
    # 2. CASO DE USO: OBTER METADADOS (AI Assisted)
    metadata_use_case = GetBookMetadataUseCase(formatter)
    
    print("\n[Etapa 1] Enviando candidatos para a IA analisar...")
    with open(book_path, "r", encoding="utf-8", errors="ignore") as f:
        full_text = f.read()
    
    # Para economizar, enviamos apenas o começo para o formatador (o extractor usa o começo para o TOC)
    # Mas como o parser atual trabalha com o texto todo, vamos passar o texto todo
    book_metadata = metadata_use_case.execute(full_text, "Moby Dick", "Herman Melville")
    
    print("\n[RESULTADO DA IA - SUMÁRIO REFINADO]:")
    toc = [ch['title'] for ch in book_metadata['chapters']]
    for i, title in enumerate(toc[:10]): # Mostra os primeiros 10
        print(f"  - {title}")
    print(f"  ... e mais {len(toc)-10} capítulos.")
    
    print(f"\n[INÍCIO SUGERIDO PELA IA]: {book_metadata['suggested_start']}")
    
    # 3. CASO DE USO: OBTER CAPÍTULO INTEGRADO COM FLOW READ
    chapter_use_case = GetBookChapterUseCase(parser)
    
    target_chapter = "CHAPTER 1. Loomings."
    print(f"\n[Etapa 2] Buscando conteúdo do capítulo: '{target_chapter}'...")
    
    chapter_content = chapter_use_case.execute(full_text, target_chapter)
    
    print("\n[CONTEÚDO DO CAPÍTULO (PREVIEW)]:")
    print("-" * 30)
    print(chapter_content[:400] + "...")
    print("-" * 30)
    
    print("\n[SUCESSO] Fluxo integrado com Clean Architecture e IA finalizado.")

if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n!!! AVISO: OPENAI_API_KEY NÃO ENCONTRADA NO AMBIENTE !!!")
        print("Tanto o teste quanto a aplicação dependem dela para o refino por IA.")
    
    test_full_ai_flow()
