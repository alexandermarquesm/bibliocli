# 📚 BiblioCLI

Uma ferramenta poderosa e unificada para buscar, baixar e formatar livros de fontes públicas como **Project Gutenberg**, **Wikisource** e **Open Library**.

Este projeto foi desenhado sob os princípios da **Clean Architecture**, servindo tanto como uma ferramenta CLI quanto como um **Motor de API** para motores de Text-to-Speech (como o [Flow-Read](https://github.com/alexandermarquesm/flow-read)).

---

## ✨ Funcionalidades

- 🔍 **Busca Multiprovedor**: Pesquise títulos ou autores simultaneamente em várias fontes bibliográficas.
- 📥 **Download e Limpeza Inteligente**: Baixa e-books e usa **IA (OpenAI)** para remover metadados, prefácios e sumários, entregando apenas o conteúdo narrativo.
- 🏗️ **Arquitetura Profissional**: Divisão clara entre Domínio, Aplicação e Infraestrutura.
- 🌐 **Modo API**: Servidor FastAPI pronto para integração com frontends e outros backends.
- 🎨 **Interface Rica**: Tabelas e logs coloridos no terminal via `Rich`.

---

## 🚀 Como Começar

### Pré-requisitos

- **Python 3.12+**
- **[uv](https://github.com/astral-sh/uv)** (Gerenciador de pacotes recomendado)

### Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/alexandermarquesm/bibliocli.git
   cd bibliocli
   ```
2. Instale as dependências:
   ```bash
   uv sync
   ```

---

## 🛠️ Modos de Uso

### 1. Interface de Linha de Comando (CLI)

O projeto define um atalho via `pyproject.toml`.

- **Buscar Livros:**
  ```bash
  uv run bibliocli search "Dom Casmurro" --book
  ```
- **Baixar um Livro:**
  ```bash
  uv run bibliocli download "URL_DO_LIVRO" --name "nome.txt"
  ```

### 2. Modo API (Integração)

Inicia um servidor FastAPI pronto para ser consumido por aplicações como o Flow-Read.

```bash
uv run bibliocli-server
```

> [!NOTE]
> Acesse `http://127.0.0.1:8000/docs` para ver a documentação interativa (Swagger).

---

## 🧠 Inteligência de Formatação (OpenAI)

Para que a limpeza automática via IA funcione, defina sua chave da API:

```bash
export OPENAI_API_KEY="sua-chave-aqui"
```

Se a chave não for fornecida, o sistema usará uma limpeza básica via Regex (fallback).

---

## 🏛️ Estrutura do Projeto (Clean Architecture)

- `src/domain`: Entidades de negócio independentes de frameworks.
- `src/application`: Regras de aplicação e interfaces (Portas).
- `src/infrastructure`: Implementações técnicas (Adaptadores):
  - `cli/`: Interface de terminal.
  - `web/`: Servidor de API e rotas.
  - `services/`: Integrações externas (OpenAI).
  - `providers/`: Adaptadores para fontes de livros.

---

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

---

_Feito por [Alexander Marques](https://github.com/alexandermarquesm)_
