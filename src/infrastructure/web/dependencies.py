from src.infrastructure.providers.gutenberg_provider import GutenbergProvider
from src.infrastructure.providers.wikisource_provider import WikisourceProvider
from src.infrastructure.providers.openlibrary_provider import OpenLibraryProvider
from src.infrastructure.services.openai_formatter import OpenAITextFormatter

# Instâncias globais que poderiam vir de um container de DI
_PROVIDERS = [
    GutenbergProvider(),
    WikisourceProvider(),
    OpenLibraryProvider()
]

_FORMATTING_AGENT = OpenAITextFormatter()

from fastapi import Request

def get_providers(request: Request):
    # No Cloudflare Workers Python, request.scope["env"] contém os bindings
    env = request.scope.get("env")
    
    # Adicionamos o binding KV à lista de providers para o controller usá-lo
    # Ou poderíamos criar uma dependência específica para o KV.
    class ProvidersContainer(list):
        def __init__(self, providers, env=None):
            super().__init__(providers)
            self.BOOKS_KV = getattr(env, "BOOKS_KV", None) if env else None

    return ProvidersContainer(_PROVIDERS, env)

def get_formatting_agent():
    return _FORMATTING_AGENT
