import sys
import os
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from rich.console import Console
from rich.table import Table
from bibliocli.domain.entities import BookSearchResult

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
        self.console.print("\n[italic]Exemplo: uv run bibliocli \"Machado de Assis\" --author[/italic]\n")

    def print_results(self, query: str, results: List[BookSearchResult], page_size: int = 5):
        if not results:
            self.console.print(f"[red]Nenhum livro encontrado nessas fontes.[/red]")
            return

        import sys
        
        # Só pagina se estivermos rodando no modo interativo (tty) e houver mais itens que o tamanho da página.
        if not sys.stdout.isatty() or len(results) <= page_size:
            self._print_page(query, results, 1, 1)
            return

        from prompt_toolkit import prompt
        from prompt_toolkit.key_binding import KeyBindings

        page = 0
        max_page = (len(results) - 1) // page_size
        
        bindings = KeyBindings()

        @bindings.add('left')
        def _(event):
            event.app.exit(result='left')

        @bindings.add('right')
        def _(event):
            event.app.exit(result='right')

        @bindings.add('enter')
        @bindings.add('q')
        @bindings.add('c-c')
        def _(event):
            event.app.exit(result='quit')

        while True:
            self.console.clear()
            
            start = page * page_size
            end = start + page_size
            current_results = results[start:end]
            
            self._print_page(query, current_results, page + 1, max_page + 1)
            
            self.console.print("\n[bold cyan]?[/bold cyan] [bold]Opções de Paginação:[/bold] [dim](Use as setas ← → para navegar ou Enter para continuar)[/dim]")
            
            try:
                res = prompt('', key_bindings=bindings)
            except KeyboardInterrupt:
                res = 'quit'
                print()
                
            if res == 'left':
                page = max(0, page - 1)
            elif res == 'right':
                page = min(max_page, page + 1)
            else:
                break
                
    def _print_page(self, query: str, current_results: List[BookSearchResult], current_page: int, total_pages: int):
        header_text = f"✨ Catálogo Localizado: [underline]'{query}'[/underline]"
        if total_pages > 1:
            header_text += f" [dim](pág. {current_page}/{total_pages})[/dim]"
            
        self.console.print(f"\n {header_text}\n")
        
        import shutil
        term_width = shutil.get_terminal_size((80, 20)).columns
        
        for i, r in enumerate(current_results):
            title_text = r.title
            
            # Limpa o status (Domínio Público / Requer Empréstimo) para o título principal se estiver poluindo muito
            # ou mantém se o usuário gostar. Vou manter mas formatar melhor.
            
            max_title_len = term_width - 6
            if len(title_text) > max_title_len > 0:
                title_text = title_text[:max_title_len - 3] + "..."
                
            self.console.print(f" [bold magenta]• {title_text}[/bold magenta]")
            
            # Monta a linha de meta-informação: Fonte | Autor | Idioma | Ano
            author = r.author if r.author else "Desconhecido"
            # Formata autor se estiver no formato "LastName, FirstName" (comum no Gutenberg)
            if "," in author:
                parts = author.split(",")
                author = f"{parts[1].strip()} {parts[0].strip()}"
                
            info_parts = [
                f"[cyan]{r.source}[/cyan]",
                f"[yellow]👤 {author}[/yellow]",
                f"[green]🌐 {r.language}[/green]"
            ]
            if r.year:
                info_parts.append(f"[white]📅 {r.year}[/white]")
                
            info_str = " [dim]|[/dim] ".join(info_parts)
            self.console.print(f"   {info_str}")
            self.console.print(f"   [blue u]{r.link}[/blue u]")
            
            if i < len(current_results) - 1:
                # Desenha uma linha discreta de separação
                line_len = min(term_width - 4, 80)
                self.console.print("   [dim]" + "─" * line_len + "[/dim]")

    def show_download_status(self, success: bool, final_path: str):
        if success:
            self.console.print(f"\n[bold green]✓ Download concluído com sucesso![/bold green]")
            self.console.print(f"Salvo em: [cyan]{final_path}[/cyan]\n")
        else:
            self.console.print("\n[bold red]✗ Falha no download.[/bold red]")
            self.console.print("Verifique se a URL enviada é suportada.\n")

    def show_restricted_book_info(self, info: BookSearchResult):
        """Mostra as informações do livro que requer empréstimo sem usar tabela."""
        self.console.print("\n[bold yellow]⚠ Este livro está protegido e requer empréstimo no Open Library.[/bold yellow]\n")
        
        import shutil
        term_width = shutil.get_terminal_size((80, 20)).columns
        
        title_text = info.title
        max_title_len = term_width - 6
        if len(title_text) > max_title_len > 0:
            title_text = title_text[:max_title_len - 3] + "..."
            
        self.console.print(f" [cyan]•[/cyan] [bold magenta]{title_text}[/bold magenta]")
        
        info_parts = [
            f"[cyan]{info.source}[/cyan]",
            f"[yellow]{info.author}[/yellow]",
            f"[green]{info.language}[/green]"
        ]
        if info.year:
            info_parts.append(f"[bold]{info.year}[/bold]")
            
        info_str = " [dim]|[/dim] ".join(info_parts)
        self.console.print(f"   {info_str}")
        self.console.print(f"   [blue u]{info.link}[/blue u]")
        
        self.console.print("\n[bold]Para acessá-lo:[/bold]")
        self.console.print(f"1. Acesse o link no seu navegador: [blue u]{info.link}[/blue u]")
        self.console.print("2. Faça login na sua conta do Internet Archive/Open Library.")
        self.console.print("3. Clique em [blue]'Borrow'[/blue] (Empréstimo).\n")
