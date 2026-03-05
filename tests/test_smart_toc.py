
import sys
import os
sys.path.append(os.getcwd())

from src.infrastructure.services.book_parser import BookParser

def test_toc_detection(filepath):
    print(f"\n--- Testando: {filepath} ---")
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    lines = text.split('\n')
    parser = BookParser()
    segments = parser.find_toc_segments(lines)
    
    if segments:
        best = segments[0]
        print(f"✅ Sumário encontrado! Linhas: {best['start']} até {best['end']}")
        print(f"Score (densidade): {best['score']}")
        print(f"Primeiros títulos detectados: {[h['title'] for h in best['headers'][:3]]}...")
        
        # Mostra as primeiras 3 linhas do segmento de texto
        preview = best['text'].split('\n')[:5]
        print(f"Texto do segmento (Preview):")
        for p in preview:
            print(f"  > {p}")
    else:
        print("❌ Nenhum sumário detectado.")

if __name__ == "__main__":
    # Testa no Dom Casmurro (índice no final)
    test_toc_detection("ebooks/Machado de Assis/Dom_Casmurro.txt")
    # Testa na Odisseia (índice no início)
    test_toc_detection("ebooks/Homer/The Odyssey Rendered into English prose for the use of those who cannot read the original.txt")
