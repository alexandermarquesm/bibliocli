from bibliocli.infrastructure.services.book_parser import BookParser

class GetBookChapterUseCase:
    """
    Caso de Uso: Obter Conteúdo de um Capítulo Específico.
    Usa Heurísticas de slicing rápido via parser para extrair
    o núcleo sem processamento pesado.
    """
    def __init__(self, parser: BookParser):
        self.parser = parser
        
    def execute(self, full_text: str, chapter_title: str) -> str:
        return self.parser.extract_chapter_content(full_text, chapter_title)
