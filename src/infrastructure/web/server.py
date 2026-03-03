import uvicorn
import argparse

def run_server():
    parser = argparse.ArgumentParser(description="BiblioCLI API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host para rodar a API")
    parser.add_argument("--port", type=int, default=8000, help="Porta para rodar a API")
    args = parser.parse_args()

    print(f"Iniciando o servidor da API em http://{args.host}:{args.port}")
    uvicorn.run("src.infrastructure.web.main:app", host=args.host, port=args.port, reload=True)

if __name__ == "__main__":
    run_server()
