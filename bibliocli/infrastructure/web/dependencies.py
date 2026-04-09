from bibliocli.infrastructure.providers.gutenberg_provider import GutenbergProvider
from bibliocli.infrastructure.providers.wikisource_provider import WikisourceProvider
from bibliocli.infrastructure.providers.openlibrary_provider import OpenLibraryProvider
from bibliocli.infrastructure.services.openai_formatter import OpenAITextFormatter

# Instâncias globais que poderiam vir de um container de DI
_PROVIDERS = [
    GutenbergProvider(),
    WikisourceProvider(),
    OpenLibraryProvider()
]

_FORMATTING_AGENT = OpenAITextFormatter()

def get_providers():
    return _PROVIDERS

def get_formatting_agent():
    return _FORMATTING_AGENT
