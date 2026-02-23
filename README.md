# 📚 BiblioCLI

Uma ferramenta de linha de comando unificada para pesquisar e baixar livros de fontes públicas e gratuitas como **WikiSource**, **Project Gutenberg** e **Open Library**.

---

## ✨ Funcionalidades

- 🔍 **Busca Poderosa**: Pesquise por títulos de livros ou autores em múltiplas fontes simultaneamente.
- 📥 **Download Direto**: Baixe e-books diretamente para sua máquina via URL.
- 🎨 **Interface Rica**: Saída visualmente organizada e colorida no terminal usando a biblioteca `Rich`.
- 🏗️ **Arquitetura Limpa**: Código estruturado seguindo princípios de Clean Architecture para fácil expansão.

---

## 🚀 Como Começar

### Pré-requisitos

- **Python 3.12+**
- **[uv](https://github.com/astral-sh/uv)** (gerenciador de pacotes rápido para Python)

### Instalação

1. Clone o repositório:

   ```bash
   git clone https://github.com/alexandermarquesm/bibliocli.git
   cd bibliocli
   ```

2. Sincronize as dependências com `uv`:
   ```bash
   uv sync
   ```

---

## 🛠️ Uso

O BiblioCLI utiliza subcomandos para facilitar a interação.

### 🔍 Buscar Livros ou Autores

Para buscar por **autor**:

```bash
uv run src/main.py search "Machado de Assis" --author
```

Para buscar por **título de livro**:

```bash
uv run src/main.py search "Dom Casmurro" --book
```

### 📥 Baixar um E-book

Utilize o comando `download` seguido da URL do livro:

```bash
uv run src/main.py download "https://pt.wikisource.org/wiki/Dom_Casmurro" --name "dom_casmurro.txt"
```

_Os livros são salvos na pasta `./ebooks/`._

---

## 🧰 Tecnologias Utilizadas

- **Python 3.12**
- **Requests**: Interação com APIs e download de conteúdo.
- **Rich**: Formatação e tabelas impressionantes no terminal.
- **Argparse**: Gerenciamento robusto de argumentos CLI.

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---

_Feito com ❤️ para amantes da literatura clássica._
