import uvicorn
import argparse
import os
from dotenv import load_dotenv

def run_server():
    load_dotenv()
    parser = argparse.ArgumentParser(description="BiblioCLI API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host para rodar a API")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)), help="Porta para rodar a API")
    args = parser.parse_args()

    print(f"Iniciando o servidor da API em http://{args.host}:{args.port}")
    uvicorn.run("src.infrastructure.web.main:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    run_server()
