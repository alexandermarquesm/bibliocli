import pytest
from unittest.mock import MagicMock
from bibliocli.application.use_cases.search_books_by_author import SearchBooksByAuthorUseCase
from bibliocli.application.interfaces import BookSearchProvider, ProviderUnavailableError

class DummySearchProvider(BookSearchProvider):
    provider_name = "Dummy"
    def search(self, query): pass
    def search_by_author(self, author): pass
    def get_popular_books(self): pass

def test_search_by_author_success():
    p1 = MagicMock(spec=DummySearchProvider)
    p1.search_by_author.return_value = ["livro1"]
    assert SearchBooksByAuthorUseCase([p1]).execute("q") == ["livro1"]

def test_search_by_author_partial_failure_generic():
    pdp = MagicMock(spec=DummySearchProvider)
    pdp.search_by_author.side_effect = Exception("Generic Crash")
    p2 = MagicMock(spec=DummySearchProvider)
    p2.search_by_author.return_value = ["l2"]
    assert SearchBooksByAuthorUseCase([pdp, p2]).execute("q") == ["l2"]

def test_search_by_author_total_failure_exception():
    p1 = MagicMock(spec=DummySearchProvider)
    p1.search_by_author.side_effect = Exception("Fail")
    assert SearchBooksByAuthorUseCase([p1]).execute("q") == []

def test_search_by_author_total_failure_provider_multiple():
    p1 = MagicMock()
    p1.search_by_author.side_effect = ProviderUnavailableError("cr")
    p1.provider_name = "p1"
    p2 = MagicMock()
    p2.search_by_author.side_effect = ProviderUnavailableError("cr")
    p2.provider_name = "p2"
    with pytest.raises(ProviderUnavailableError) as err:
        SearchBooksByAuthorUseCase([p1, p2]).execute("q")
    assert "Todos os provedores de busca por autor falharam:" in str(err.value)

def test_search_by_author_total_failure_provider_single():
    p1 = MagicMock()
    p1.search_by_author.side_effect = ProviderUnavailableError("single crash")
    p1.provider_name = "p1"
    with pytest.raises(ProviderUnavailableError) as err:
        SearchBooksByAuthorUseCase([p1]).execute("q")
    assert "single crash" in str(err.value)
