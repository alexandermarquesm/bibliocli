import pytest
from unittest.mock import MagicMock
import json
from bibliocli.application.use_cases.get_book_metadata import GetBookMetadataUseCase
from bibliocli.application.interfaces import BookTextFormatter

class DummyFormatter(BookTextFormatter):
    def format_text(self, raw_text: str, source: str, title: str = None, author: str = None) -> str:
        pass

def test_get_metadata_success():
    fmt = MagicMock(spec=DummyFormatter)
    fmt.format_text.return_value = '{"title": "Test"}'
    
    uc = GetBookMetadataUseCase(fmt)
    assert uc.execute("raw", "T", "A") == {"title": "Test"}

def test_get_metadata_throws_clean_runtime_error():
    fmt = MagicMock(spec=DummyFormatter)
    fmt.format_text.return_value = 'invalido { texto'
    
    uc = GetBookMetadataUseCase(fmt)
    with pytest.raises(RuntimeError) as exc:
        uc.execute("raw", "T", "A")
    assert "O formatador falhou em retornar um JSON válido:" in str(exc.value)
