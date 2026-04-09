import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import os
import json

from typing import Union, List
from bibliocli.application.use_cases.get_or_format_book_use_case import GetOrFormatBookUseCase
from bibliocli.application.interfaces import BookDownloadProvider, BookTextFormatter, IBookRepository
from bibliocli.domain.entities import BookSearchResult

class DummyDownloadProvider(BookDownloadProvider):
    def can_download(self, url: str) -> bool: pass
    def download(self, url: str, destiny_path: str) -> bool: pass
    def get_info(self, url: str) -> BookSearchResult: pass

class DummyFormatter(BookTextFormatter):
    def format_text(self, raw_text: Union[str, bytes], source: str, title: str = None, author: str = None) -> str: pass

class DummyRepository(IBookRepository):
    async def find_by_url(self, url: str) -> dict: pass
    async def find_formatted(self, author: str, title: str) -> dict: pass
    async def save(self, book) -> str: pass

@pytest.fixture
def mocks():
    provider = MagicMock(spec=DummyDownloadProvider)
    formatter = MagicMock(spec=DummyFormatter)
    repo = AsyncMock(spec=DummyRepository)
    
    provider.can_download.return_value = True
    provider.get_info.return_value = BookSearchResult(
        source="Test", title="Test Title", author="Test Author", language="PT", link="http://test.com", cover_url="test.jpg", year="2000"
    )
    provider.download.return_value = True
    formatter.format_text.return_value = json.dumps({"title": "Test Title", "author": "Test Author", "language": "PT", "chapters": []})
    repo.find_by_url.return_value = None
    repo.find_formatted.return_value = None
    
    return provider, formatter, repo

@pytest.fixture
def use_case(mocks):
    provider, formatter, repo = mocks
    return GetOrFormatBookUseCase([provider], formatter, repo)

@pytest.mark.asyncio
async def test_execute_no_provider_supports_url(use_case, mocks):
    provider, _, _ = mocks
    provider.can_download.return_value = False
    res, err = await use_case.execute("http://unknown.com")
    assert res is None
    assert "Nenhum provedor suporta o download" in err

@pytest.mark.asyncio
async def test_execute_cache_hit_by_url(use_case, mocks):
    provider, _, repo = mocks
    repo.find_by_url.return_value = {"chapters": [{"title": "cap1"}]}
    res, err = await use_case.execute("http://cache.com")
    assert err is None
    assert res["formatted_content"] == {"chapters": [{"title": "cap1"}]}

@pytest.mark.asyncio
async def test_execute_cache_hit_by_author_title(use_case, mocks):
    _, _, repo = mocks
    repo.find_by_url.return_value = None
    repo.find_formatted.return_value = {"chapters": [{"title": "cap2"}]}
    res, err = await use_case.execute("http://cache2.com")
    assert err is None
    assert res["formatted_content"] == {"chapters": [{"title": "cap2"}]}

@pytest.mark.asyncio
async def test_execute_download_fails(use_case, mocks):
    provider, _, _ = mocks
    provider.download.return_value = False
    with patch("os.path.exists", return_value=True), patch("os.remove") as mock_remove:
        res, err = await use_case.execute("http://fail.com")
        assert res is None
        assert "Falha ao baixar" in err
        mock_remove.assert_called_once()

@pytest.mark.asyncio
async def test_execute_full_flow_success_txt(use_case, mocks):
    provider, formatter, repo = mocks
    
    # Simular fluxos de abertura de arquivo:
    # 1. rb para o cabeçalho (magic number) -> não é ZIP
    # 2. r para ler o texto
    mock_files = {
        # rb (bytes)
        "rb": MagicMock(),
        # r (str)
        "r": MagicMock()
    }
    mock_files["rb"].__enter__.return_value.read.return_value = b"NotA"
    mock_files["r"].__enter__.return_value.read.return_value = "raw text content"

    def side_effect(path, mode="r", **kwargs):
        return mock_files[mode]

    with patch("builtins.open", side_effect=side_effect), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove") as mock_remove:
        
        res, err = await use_case.execute("http://success.com")
        
        assert err is None
        assert res["book_url"] == "http://success.com"
        # O formatador heurístico (fallback) deve ter sido chamado com a string
        formatter.format_text.assert_called_once_with("raw text content", "DummyDownloadProvider", title="Test Title", author="Test Author")
        repo.save.assert_called_once()
        mock_remove.assert_called_once()
        
@pytest.mark.asyncio
async def test_execute_handles_exceptions_safely(use_case, mocks):
    provider, _, _ = mocks
    provider.get_info.side_effect = Exception("Crash")
    
    with patch("os.path.exists", return_value=True), patch("os.remove", side_effect=Exception("Remove failed")):
        res, err = await use_case.execute("http://crash.com")
        assert res is None
        assert "Erro inesperado" in err
