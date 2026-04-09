import pytest
from unittest.mock import MagicMock
from bibliocli.application.use_cases.get_popular_books import GetPopularBooksUseCase
from bibliocli.application.interfaces import BookSearchProvider, ProviderUnavailableError

class DummySearchProvider(BookSearchProvider):
    provider_name = "Dummy"
    def search(self, query): pass
    def search_by_author(self, author): pass
    def get_popular_books(self): pass

def test_get_popular_success():
    p1 = MagicMock(spec=DummySearchProvider)
    p1.get_popular_books.return_value = ["livro1"]
    assert GetPopularBooksUseCase([p1]).execute() == ["livro1"]

def test_get_popular_partial_failure():
    p1 = MagicMock(spec=DummySearchProvider)
    p1.get_popular_books.side_effect = Exception("Fail")
    p2 = MagicMock(spec=DummySearchProvider)
    p2.get_popular_books.return_value = ["l2"]
    assert GetPopularBooksUseCase([p1, p2]).execute() == ["l2"]

def test_get_popular_total_failure_exception():
    p1 = MagicMock(spec=DummySearchProvider)
    p1.get_popular_books.side_effect = Exception("Fail")
    assert GetPopularBooksUseCase([p1]).execute() == []

def test_get_popular_total_failure_provider_multiple():
    p1 = MagicMock()
    p1.get_popular_books.side_effect = ProviderUnavailableError("cr")
    p1.provider_name = "p1"
    p2 = MagicMock()
    p2.get_popular_books.side_effect = ProviderUnavailableError("cr")
    p2.provider_name = "p2"
    with pytest.raises(ProviderUnavailableError) as err:
        GetPopularBooksUseCase([p1, p2]).execute()
    assert "Todos os provedores de populares falharam:" in str(err.value)

def test_get_popular_total_failure_provider_single():
    p1 = MagicMock()
    p1.get_popular_books.side_effect = ProviderUnavailableError("single crash")
    p1.provider_name = "p1"
    with pytest.raises(ProviderUnavailableError) as err:
        GetPopularBooksUseCase([p1]).execute()
    assert "single crash" in str(err.value)
