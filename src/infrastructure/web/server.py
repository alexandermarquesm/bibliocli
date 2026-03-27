import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    """
    Entry point for the BiblioCLI Web HUD server.
    """
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Iniciando BiblioCLI Server em http://{host}:{port}")
    uvicorn.run("src.infrastructure.web.main:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    main()
