
import re
import json
import pytest
from src.infrastructure.services.book_parser import BookParser
from src.infrastructure.services.openai_formatter import OpenAITextFormatter

class TestModularBookParsing:
    """
    Suite de testes para validar a nova arquitetura modular de parsing.
    """
    
    @pytest.fixture
    def parser(self):
        return BookParser()

    @pytest.fixture
    def formatter(self):
        return OpenAITextFormatter()

    @pytest.fixture
    def odyssey_text(self):
        path = "/home/gangplank/projects/bibliocli/ebooks/Homer -750--650/The Odyssey Rendered into English prose for the use of those who cannot read the original.txt"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_modular_toc_extraction(self, parser, odyssey_text):
        """Valida que o serviço especializado identifica o sumário corretamente."""
        lines = odyssey_text.split('\n')
        trusted_titles = parser.extract_toc_titles(lines)
        
        assert len(trusted_titles) > 10
        assert "book i" in trusted_titles
        assert "book xxiv" in trusted_titles
        assert "contents" in trusted_titles

    def test_chapter_4_modular_extraction(self, formatter, odyssey_text):
        """Valida a extração do Livro IV (Capítulo 4) usando o formatador refatorado."""
        formatted_json = formatter.format_text(odyssey_text)
        data = json.loads(formatted_json)
        
        chapters = data["chapters"]
        # Procuramos o BOOK IV que seja narrativo
        chapter_4 = next((c for c in chapters if "BOOK IV" in c["title"].upper() and c["is_narrative"]), None)
        
        assert chapter_4 is not None
        assert len(chapter_4["paragraphs"]) > 5
        
        # Verifica conteúdo específico narrativo da Odisseia
        first_para = chapter_4["paragraphs"][0]
        assert any(word.lower() in first_para.lower() for word in ["Lacedaemon", "Menelaus", "Sparta"])

    def test_suggested_start_skips_preface(self, formatter, odyssey_text):
        """Valida que a aplicação modular pula os prefácios ao sugerir o início."""
        formatted_json = formatter.format_text(odyssey_text)
        data = json.loads(formatted_json)
        
        start_idx = data["suggested_start"]["chapter_index"]
        start_chapter = data["chapters"][start_idx]
        
        # O início sugerido DEVE ser o Book I, não o Preface ou Contents
        assert "BOOK I" in start_chapter["title"].upper()
        assert not any(k in start_chapter["title"].lower() for k in ["preface", "contents"])
