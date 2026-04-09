import io
import re
import weakref
from typing import List, Dict, Any, Union
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
import ebooklib
from ebooklib import epub

# Ignorar o aviso de XML parseado como HTML, pois EPUBs são XHTML/XML
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from bibliocli.application.interfaces import BookTextFormatter
from bibliocli.domain.models.book_models import Chapter

class EpubFormatter(BookTextFormatter):
    """
    Formatador de livros estruturado que processa arquivos EPUB.
    Utiliza as âncoras XML (HTML5/XHTML) reais para recuperar parágrafos 
    100% íntegros e capítulos com metadados perfeitamente enquadrados.
    """

    def format_text(self, raw_data: Union[str, bytes], source: str = "EPUB", title: str = None, author: str = None, only_toc: bool = False) -> str:
        """
        Recebe os bytes brutos do EPUB (para processamento In-Memory) ou o caminho para o arquivo.
        """
        if isinstance(raw_data, str):
            # Fallback de segurança se mandarem o caminho local pra testes
            try:
                with open(raw_data, "rb") as f:
                    epub_bytes = f.read()
            except IOError:
                # Se for apenas uma string de lixo, nós não podemos fazer nada
                raise ValueError("O EpubFormatter requer bytes ou o caminho para um arquivo .epub válido.")
        else:
            epub_bytes = raw_data

        # Instancia o arquivo ZIP/EPUB puro da Memória! Sem salvamentos nocivos na Vercel
        mem_file = io.BytesIO(epub_bytes)
        book = epub.read_epub(mem_file)

        chapters = []
        
        # A Navegação nativa do epub garante que vamos varrer os documentos HTML
        # na ordem exata de leitura estipulada pelo publicador (Spine)
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            # item.get_content() retorna o HTML bytes cru
            html_content = item.get_content()
            soup = BeautifulSoup(html_content, 'lxml-xml')

            # Tenta inferir o título da sessão por headers nativos ou tag <title>
            title_node = soup.find(['h1', 'h2', 'h3'])
            if title_node:
                # Remove espaços duplos ou newlines sujas (as vezes o título envolve 2 tags)
                chapter_title = " ".join(title_node.get_text(separator=' ').split())
            else:
                head_title = soup.find('title')
                chapter_title = head_title.get_text().strip() if head_title else "Documento Não Intitulado"

            paragraphs_nodes = soup.find_all('p')
            
            cleaned_paras = []
            for p in paragraphs_nodes:
                # Transforma quebras de tags internas em espaços
                text = p.get_text(separator=' ')
                # Normaliza N espaços, quebras de linhas ou \t para um espaço
                clean_text = " ".join(text.split())
                if clean_text:
                    cleaned_paras.append(clean_text)

            # Ignorar capítulos que são claramente metadados do Project Gutenberg
            gutenberg_noise = [
                "Project Gutenberg eBook of",
                "Project Gutenberg eBook"
            ]
            is_noise = any(noise in chapter_title for noise in gutenberg_noise)
            
            # Checar também o conteúdo do primeiro parágrafo por padrões de metadados
            if cleaned_paras:
                first_para = cleaned_paras[0].lower()
                if "title :" in first_para and "author :" in first_para:
                    is_noise = True

            # Remover separadores inúteis no início e no fim do capítulo
            # (Ex: asteriscos que sobram no fim de um arquivo HTML do EPUB)
            separator_pattern = re.compile(r'^[\s\*\.\-\—]*[\*\.\-\—][\s\*\.\-\—]*$')
            
            # Limpar o fim
            while cleaned_paras and separator_pattern.match(cleaned_paras[-1]):
                cleaned_paras.pop()
            
            # Limpar o início
            while cleaned_paras and separator_pattern.match(cleaned_paras[0]):
                cleaned_paras.pop(0)

            # Normalizar separadores no meio (opcional, para ficar mais elegante)
            for i in range(len(cleaned_paras)):
                if separator_pattern.match(cleaned_paras[i]):
                    cleaned_paras[i] = "* * *"

            # Só adicionamos como capítulo se tiver conteúdo literário útil e não for ruído
            if len(cleaned_paras) > 0 and not is_noise:
                chapters.append(Chapter(
                    title=chapter_title,
                    paragraphs=cleaned_paras,
                    is_narrative=True,
                    index=len(chapters)
                ))

        # Correção Semântica: se há centenas de pequenos arquivos sem titulo (Ex. Gutenberg fatiando preface em 20 pedaços)
        from bibliocli.domain.models.book_models import FormattedBook
        book_data = FormattedBook(
            title=title or "Título Desconhecido",
            author=author or "Autor Desconhecido",
            chapters=chapters,
            suggested_start={"chapter_index": 0, "paragraph_index": 0} 
        )

        import json
        return json.dumps(book_data.model_dump(), indent=2, ensure_ascii=False)
