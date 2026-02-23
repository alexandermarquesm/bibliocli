import argparse
import sys
import os

# Adiciona a raiz do projeto no path para encontrar o pacote src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa o core (Use Cases)
from src.application.use_cases import SearchBooksUseCase, SearchBooksByAuthorUseCase
from src.application.download_use_cases import DownloadBookUseCase

# Importa as implementações externas (Providers)
from src.infrastructure.providers.wikisource_provider import WikisourceProvider
from src.infrastructure.providers.gutenberg_provider import GutenbergProvider
from src.infrastructure.providers.openlibrary_provider import OpenLibraryProvider

# Importa a GUI/Presentation
from src.presentation.cli_formatter import CLIFormatter

def main():
    parser = argparse.ArgumentParser(description="Biblioteca Digital CLI")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando Search
    search_parser = subparsers.add_parser("search", help="Busca livros ou autores")
    search_parser.add_argument("termo", help="Termo de busca")
    group = search_parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--author", action="store_true", help="Busca por autor")
    group.add_argument("--book", action="store_true", help="Busca por livro")

    # Comando Download
    download_parser = subparsers.add_parser("download", help="Baixa um livro pela URL")
    download_parser.add_argument("url", help="URL do e-book")
    download_parser.add_argument("--name", help="Nome do arquivo (opcional)", default=None)

    args = parser.parse_args()
    cli = CLIFormatter()

    if not args.command:
        cli.show_usage_hint()
        sys.exit(0)

    providers = [
        WikisourceProvider(),
        GutenbergProvider(),
        OpenLibraryProvider()
    ]

    if args.command == "search":
        if not args.author and not args.book:
            cli.show_usage_hint()
            return

        if args.author:
            use_case = SearchBooksByAuthorUseCase(providers=providers)
            with cli.console.status(f"[bold green]Procurando por autor '{args.termo}'...[/bold green]"):
                resultados = use_case.execute(args.termo)
        else:
            use_case = SearchBooksUseCase(providers=providers)
            with cli.console.status(f"[bold green]Procurando pelo livro '{args.termo}'...[/bold green]"):
                resultados = use_case.execute(args.termo)
        cli.print_results(args.termo, resultados)

    elif args.command == "download":
        # Filtra dinamicamente quem implementa a interface de download
        from src.application.interfaces import BookDownloadProvider, RestrictedBookError
        download_providers = [p for p in providers if isinstance(p, BookDownloadProvider)]
        
        use_case = DownloadBookUseCase(providers=download_providers)
        destiny_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "ebooks")
        os.makedirs(destiny_dir, exist_ok=True)

        try:
            with cli.console.status(f"[bold blue]Analisando URL e Iniciando Download...[/bold blue]"):
                sucesso, final_path = use_case.execute(args.url, destiny_dir, name=args.name)
            
            # Note: Se sucesso for False e não lançou exceção, é uma falha comum
            cli.show_download_status(sucesso, final_path)
        except RestrictedBookError as e:
            cli.show_restricted_book_info(e.info)
        except Exception as e:
            cli.console.print(f"[bold red]Erro inesperado:[/bold red] {e}")

if __name__ == "__main__":
    main()
