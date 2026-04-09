import sys
import urllib.request
import json
import os

# Adiciona o src/ do projeto ao PYTHONPATH para não dar erros de import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from bibliocli.infrastructure.services.heuristic_formatter import HeuristicTextFormatter

def main():
    if len(sys.argv) < 2:
        print("Uso correto: python test_manual_toc_inspector.py <ID_DO_LIVRO>")
        print("Exemplo para Alice: python test_manual_toc_inspector.py 11")
        print("Exemplo para Frankenstein: python test_manual_toc_inspector.py 84")
        return
        
    book_id = sys.argv[1]
    # O Padrão URL textual do Gutenberg comumente termina em -0.txt para UTF-8. 
    # Caso um não exista, tentamos a raiz sem o -0.
    url_base = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"
    url_fallback = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    
    print(f"Baixando o livro ID {book_id} do Project Gutenberg...\n")
    try:
        text = urllib.request.urlopen(url_base).read().decode("utf-8")
    except urllib.error.HTTPError:
        print("Tentando o link de fallback...")
        text = urllib.request.urlopen(url_fallback).read().decode("utf-8")
    except Exception as e:
        print(f"Erro global de download: {e}")
        return
        
    formatter = HeuristicTextFormatter()
    
    # Chama nossa super função para extrair TUDO (TOC guiando os Capítulos)
    json_string = formatter.format_text(
        raw_text=text, 
        source="Gutenberg", 
        title=f"Book {book_id}",
        only_toc=False
    )
    
    output_path = os.path.join(os.path.dirname(__file__), f"output_book_{book_id}_full.json")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json_string)
        
    print(f"\n[SUCESSO ABSOLUTO] Sumário e Capítulos fatiados perfeitamente salvos em:")
    print(f"-> {output_path}")

if __name__ == "__main__":
    main()

