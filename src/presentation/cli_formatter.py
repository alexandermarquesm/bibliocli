import sys
import os
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from rich.console import Console
from rich.table import Table
from src.domain.entities import BookSearchResult

class CLIFormatter:
    """
    Camada de Apresentação (Presentation).
    Isolada de detalhes de como o livro foi buscado. Entende apenas que recebe
    uma lista de objetos `BookSearchResult` e sabe desenhar uma tabela Rich no terminal.
    """
    def __init__(self):
        self.console = Console()

    def show_usage_hint(self):
        self.console.print("\n[bold cyan]Boas-vindas ao Buscador de Livros![/bold cyan] 📚")
        self.console.print("\nPara que eu possa te ajudar a encontrar o que procura, por favor escolha uma das opções:")
        self.console.print("  • Se estiver buscando por um autor: [bold blue]--author[/bold blue]")
        self.console.print("  • Se estiver buscando por um livro: [bold blue]--book[/bold blue]")
        self.console.print("\n[italic]Exemplo: uv run src/main.py \"Machado de Assis\" --author[/italic]\n")

    def print_results(self, query: str, results: List[BookSearchResult]):
        table = Table(title=f"Resultados de Busca: '{query}'")

        table.add_column("Fonte", style="cyan", no_wrap=True)
        table.add_column("Livro", style="magenta")
        table.add_column("Idioma(s)", style="green")
        table.add_column("Link (URL)", style="blue")

        if not results:
            self.console.print("[red]Nenhum livro encontrado nessas fontes.[/red]")
        else:
            for r in results:
                table.add_row(r.source, r.title, r.language, r.link)
            
            self.console.print(table)

    def show_download_status(self, success: bool, final_path: str):
        if success:
            self.console.print(f"\n[bold green]✓ Download concluído com sucesso![/bold green]")
            self.console.print(f"Salvo em: [cyan]{final_path}[/cyan]\n")
        else:
            self.console.print("\n[bold red]✗ Falha no download.[/bold red]")
            self.console.print("Verifique se a URL enviada é suportada.\n")
