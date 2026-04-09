import pytest
from unittest.mock import MagicMock
from bibliocli.application.use_cases.get_book_chapter import GetBookChapterUseCase
from bibliocli.infrastructure.services.book_parser import BookParser

def test_get_book_chapter():
    parser_mock = MagicMock(spec=BookParser)
    parser_mock.extract_chapter_content.return_value = "content"
    
    uc = GetBookChapterUseCase(parser_mock)
    
    assert uc.execute("full text", "Chapter 1") == "content"
    parser_mock.extract_chapter_content.assert_called_once_with("full text", "Chapter 1")
