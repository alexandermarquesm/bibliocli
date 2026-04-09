import asyncio
import os
import json
import sys
import pytest
from bibliocli.application.use_cases.get_or_format_book_use_case import GetOrFormatBookUseCase
from bibliocli.infrastructure.providers.gutenberg_provider import GutenbergProvider
from bibliocli.infrastructure.services.heuristic_formatter import HeuristicTextFormatter
from bibliocli.application.interfaces import IBookRepository
from bibliocli.domain.models.book_models import FormattedBook

# Mock Repository to avoid database dependency during test
class MockRepository(IBookRepository):
    async def find_by_url(self, url): return None
    async def find_formatted(self, author, title): return None
    async def save(self, book): pass
    async def close(self): pass
    async def setup(self): pass

@pytest.mark.asyncio
async def test_epub_flow():
    # Permitir passar a URL ou ID via argumento (Ex: python test.py 84 ou python test.py https://...)
    # Quando rodado via pytest, sys.argv[1] pode ser um caminho ou flag.
    target = "https://www.gutenberg.org/ebooks/11"
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-') and "pytest" not in sys.argv[0]:
        target = sys.argv[1]
    
    # Se passar só o número, completa a URL
    if target.isdigit():
        target = f"https://www.gutenberg.org/ebooks/{target}"
        
    alice_url = target
    
    # Setup
    provider = GutenbergProvider()
    heuristic_formatter = HeuristicTextFormatter()
    repo = MockRepository()
    
    use_case = GetOrFormatBookUseCase(
        providers=[provider],
        formatter=heuristic_formatter,
        repository=repo
    )
    
    print(f"--- Iniciando Teste de Fluxo EPUB para: {alice_url} ---")
    
    # Executar (isso vai baixar o EPUB, detectar, usar o EpubFormatter e retornar o JSON)
    result, error = await use_case.execute(alice_url)
    
    if error:
        print(f"❌ Erro detectado: {error}")
        return

    formatted_content = result.get("formatted_content", {})
    chapters = formatted_content.get("chapters", [])
    
    print(f"✅ Sucesso! Livro processado.")
    print(f"📖 Título: {formatted_content.get('title')}")
    print(f"✍️ Autor: {formatted_content.get('author')}")
    print(f"🔖 Total de Capítulos: {len(chapters)}")
    
    if chapters:
        first_ch = chapters[0]
        print(f"\nExemplo do Primeiro Capítulo ('{first_ch.get('title')}'):")
        paras = first_ch.get("paragraphs", [])
        print(f"📝 Parágrafos: {len(paras)}")
        if paras:
            print(f"📄 Início do Texto: {paras[0][:150]}...")

    # Gerar nome de arquivo dinâmico baseado no título e ID
    import re
    book_id = re.search(r'ebooks/(\d+)', alice_url).group(1) if re.search(r'ebooks/(\d+)', alice_url) else "unknown"
    title_safe = "".join([c for c in formatted_content.get('title', 'book') if c.isalnum() or c == ' ']).strip().replace(' ', '_')
    
    filename = f"output_book_{book_id}_{title_safe}.json"
    output_file = f"/home/gangplank/projects/bibliocli/tests/outputs/{filename}"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n📂 Resultado completo salvo em: {output_file}")

if __name__ == "__main__":
    asyncio.run(test_epub_flow())
