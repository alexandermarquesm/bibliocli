import pytest
from unittest.mock import MagicMock
from bibliocli.application.use_cases.search_books import SearchBooksUseCase
from bibliocli.application.interfaces import BookSearchProvider, ProviderUnavailableError

class DummySearchProvider(BookSearchProvider):
    provider_name = "Dummy"
    def search(self, query): pass
    def search_by_author(self, author): pass
    def get_popular_books(self): pass

def test_search_books_success():
    p1 = MagicMock(spec=DummySearchProvider)
    p1.search.return_value = ["livro1"]
    assert SearchBooksUseCase([p1]).execute("q") == ["livro1"]

def test_search_books_partial_failure_provider_unavailable():
    pdp = MagicMock(spec=DummySearchProvider)
    pdp.search.side_effect = ProviderUnavailableError("Crashed")
    p2 = MagicMock(spec=DummySearchProvider)
    p2.search.return_value = ["l2"]
    assert SearchBooksUseCase([pdp, p2]).execute("q") == ["l2"]

def test_search_books_partial_failure_generic_exception():
    pdp = MagicMock(spec=DummySearchProvider)
    pdp.search.side_effect = Exception("Generic Crash")
    p2 = MagicMock(spec=DummySearchProvider)
    p2.search.return_value = ["l2"]
    assert SearchBooksUseCase([pdp, p2]).execute("q") == ["l2"]

def test_search_books_total_failure_generic_exception():
    pdp = MagicMock(spec=DummySearchProvider)
    pdp.search.side_effect = Exception("General Crash")
    pdp.provider_name = "p1"
    # Silence happens when we catch Exception and don't append to failed_providers.
    # Therefore, combined_results = [], failed_providers = []
    # return combined_results -> []
    assert SearchBooksUseCase([pdp]).execute("q") == []

def test_search_books_total_failure_provider_unavailable_multiple():
    p1 = MagicMock(spec=DummySearchProvider)
    p1.search.side_effect = ProviderUnavailableError("cr")
    p1.provider_name = "p1"
    p2 = MagicMock(spec=DummySearchProvider)
    p2.search.side_effect = ProviderUnavailableError("cr")
    p2.provider_name = "p2"
    with pytest.raises(ProviderUnavailableError) as err:
        SearchBooksUseCase([p1, p2]).execute("q")
    assert "Todos os provedores de busca falharam" in str(err.value)

def test_search_books_total_failure_provider_unavailable_single():
    p1 = MagicMock(spec=DummySearchProvider)
    p1.search.side_effect = ProviderUnavailableError("single crash")
    p1.provider_name = "p1"
    with pytest.raises(ProviderUnavailableError) as err:
        SearchBooksUseCase([p1]).execute("q")
    assert "single crash" in str(err.value)
