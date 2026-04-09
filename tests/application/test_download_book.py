import pytest
from unittest.mock import MagicMock
from bibliocli.application.use_cases.download_book import DownloadBookUseCase
from bibliocli.application.interfaces import BookDownloadProvider
from bibliocli.domain.entities import BookSearchResult

class DummyDownloadProvider(BookDownloadProvider):
    def can_download(self, url: str) -> bool: pass
    def download(self, url: str, destiny_path: str) -> bool: pass
    def get_info(self, url: str) -> BookSearchResult: pass

def test_download_book_no_provider():
    p1 = MagicMock(spec=DummyDownloadProvider)
    p1.can_download.return_value = False
    uc = DownloadBookUseCase([p1])
    success, destiny = uc.execute("u", "/t")
    assert success is False

def test_download_book_success_and_ends_with_txt(tmp_path):
    p1 = MagicMock(spec=DummyDownloadProvider)
    p1.can_download.return_value = True
    p1.get_info.return_value = BookSearchResult(source="S", title="Meu Livro", author="A", language="PT", link="L", cover_url="C")
    p1.download.return_value = True
    
    uc = DownloadBookUseCase([p1])
    success, path = uc.execute("u", str(tmp_path), name="MeuLivro.txt")
    assert success is True
    assert path.endswith("MeuLivro.txt")

def test_download_book_success_no_text_sanitize(tmp_path):
    p1 = MagicMock(spec=DummyDownloadProvider)
    p1.can_download.return_value = True
    p1.get_info.return_value = BookSearchResult(source="S", title="", author="", language="PT", link="L", cover_url="C")
    p1.download.return_value = True
    
    uc = DownloadBookUseCase([p1])
    # Passando none p/ name força sanitize de title vazio e autor vazio
    success, path = uc.execute("u", str(tmp_path))
    assert success is True
    assert "unknown.txt" in path
    assert "unknown" in path

def test_download_book_exception(tmp_path):
    p1 = MagicMock(spec=DummyDownloadProvider)
    p1.can_download.return_value = True
    p1.get_info.side_effect = Exception("Crash in provider")
    
    uc = DownloadBookUseCase([p1])
    with pytest.raises(Exception):
        uc.execute("u", str(tmp_path))
