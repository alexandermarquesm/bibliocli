import argparse
import sys
import os

from src.presentation.controllers.book_controller import BookController
from src.application.download_use_cases import DownloadBookUseCase

from src.infrastructure.providers.wikisource_provider import WikisourceProvider
from src.infrastructure.providers.gutenberg_provider import GutenbergProvider
from src.infrastructure.providers.openlibrary_provider import OpenLibraryProvider

from src.infrastructure.cli.cli_formatter import CLIFormatter

def run_cli():
    parser = argparse.ArgumentParser(description="Biblioteca Digital CLI")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando Search
    search_parser = subparsers.add_parser("search", help="Busca livros ou autores via CLI")
    search_parser.add_argument("termo", help="Termo de busca")
    group = search_parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--author", action="store_true", help="Busca por autor")
    group.add_argument("--book", action="store_true", help="Busca por livro")

    # Comando Download
    download_parser = subparsers.add_parser("download", help="Baixa um livro pela URL via CLI")
    download_parser.add_argument("url", help="URL do e-book")
    download_parser.add_argument("--name", help="Nome do arquivo (opcional)", default=None)

    args = parser.parse_args()
    cli = CLIFormatter()

    if not args.command:
        run_interactive_mode(cli)
        sys.exit(0)

    # Lógica CLI Padrão
    providers = [
        WikisourceProvider(),
        GutenbergProvider(),
        OpenLibraryProvider()
    ]

    if args.command == "search":
        if not args.author and not args.book:
            cli.show_usage_hint()
            return

        controller = BookController(providers)
        search_type = "author" if args.author else "book"
        status_msg = f"[bold green]Procurando por {search_type} '{args.termo}'...[/bold green]"
        
        with cli.console.status(status_msg):
            resultados = controller.get_search_results(args.termo, search_type=search_type)
            
        cli.print_results(args.termo, resultados)

    elif args.command == "download":
        from src.application.interfaces import BookDownloadProvider, RestrictedBookError
        download_providers = [p for p in providers if isinstance(p, BookDownloadProvider)]
        
        use_case = DownloadBookUseCase(providers=download_providers)
        destiny_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "..", "..", "ebooks")
        os.makedirs(destiny_dir, exist_ok=True)

        try:
            with cli.console.status(f"[bold blue]Analisando URL e Iniciando Download...[/bold blue]"):
                sucesso, final_path = use_case.execute(args.url, destiny_dir, name=args.name)
            
            cli.show_download_status(sucesso, final_path)
        except RestrictedBookError as e:
            cli.show_restricted_book_info(e.info)
        except Exception as e:
            cli.console.print(f"[bold red]Erro inesperado:[/bold red] {e}")

def run_interactive_mode(cli):
    import questionary
    from rich.panel import Panel
    from rich.console import Console
    from src.application.interfaces import BookDownloadProvider, RestrictedBookError
    
    # "por enquanto só o do the project gutenberg vai estar funcionando"
    providers = [GutenbergProvider()]
    
    cli.console.print(
        Panel.fit(
            "[bold cyan]📚 Biblioteca Digital CLI Interativa[/bold cyan]\n"
            "[dim]Busque e baixe livros de domínio público de forma elegante\n"
            "Pressione [bold red]Ctrl+C[/bold red] a qualquer momento para sair.[/dim]",
            border_style="cyan"
        )
    )
    
    custom_style = questionary.Style([
        ('qmark', 'fg:#00d7d7 bold'),       # cyan
        ('question', 'bold'),               # default text but bold
        ('answer', 'fg:#00d700 bold'),      # green
        ('pointer', 'fg:#d700d7 bold'),     # magenta
        ('highlighted', 'fg:#00d7d7 bold'), # cyan
        ('instruction', 'fg:#808080 italic')# dark gray
    ])
    
    while True:
        try:
            print("\n") # Espaço para separar as rodadas
            acao = questionary.select(
                "O que você deseja fazer?",
                choices=[
                    questionary.Choice("🔍 Procurar um livro ou autor", value="procurar"),
                    questionary.Choice("📥 Baixar um livro a partir de um link", value="baixar"),
                    questionary.Choice("❌ Sair", value="sair")
                ],
                style=custom_style,
                instruction="(Use as setas ↑ ↓)"
            ).ask()
            
            if not acao or acao == "sair":
                cli.console.print("[dim]Saindo da Biblioteca Digital CLI. Até mais![/dim]")
                break
            
            if acao == "procurar":
                tipo = questionary.select(
                    "Procurar por:",
                    choices=[
                        questionary.Choice("📖 Livro", value="livro"),
                        questionary.Choice("✍️  Autor", value="autor")
                    ],
                    style=custom_style,
                    instruction="(Use as setas ↑ ↓)"
                ).ask()
                
                if not tipo:
                    continue
                    
                termo = questionary.text(
                    f"Digite o nome do {'livro' if tipo == 'livro' else 'autor'}:",
                    style=custom_style
                ).ask()
                
                if not termo:
                    continue
                
                controller = BookController(providers)
                status_msg = f"[bold green]Procurando por {tipo} '{termo}'...[/bold green]"
                
                with cli.console.status(status_msg):
                    resultados = controller.get_search_results(termo, search_type="author" if tipo == "autor" else "book")
                        
                cli.print_results(termo, resultados)
                
                if not resultados:
                     cli.console.print(f"[yellow]Nenhum resultado encontrado para o {tipo} '{termo}'.[/yellow]")
                
            elif acao == "baixar":
                url = questionary.text(
                    "Digite o link do e-book para baixar (Project Gutenberg):",
                    style=custom_style
                ).ask()
                
                if not url:
                    continue
                    
                download_providers = [p for p in providers if isinstance(p, BookDownloadProvider)]
                use_case = DownloadBookUseCase(providers=download_providers)
                destiny_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "..", "..", "ebooks")
                os.makedirs(destiny_dir, exist_ok=True)
                
                try:
                    with cli.console.status(f"[bold blue]Analisando URL e Iniciando Download...[/bold blue]"):
                        sucesso, final_path = use_case.execute(url, destiny_dir, name=None)
                    
                    cli.show_download_status(sucesso, final_path)
                except RestrictedBookError as e:
                    cli.show_restricted_book_info(e.info)
                except Exception as e:
                    cli.console.print(f"[bold red]Erro inesperado:[/bold red] {e}")

        except KeyboardInterrupt:
            cli.console.print("\n[dim]Saindo da Biblioteca Digital CLI. Até mais![/dim]")
            break

if __name__ == "__main__":
    run_cli()
