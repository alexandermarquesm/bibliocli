from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from src.infrastructure.web.routes import search, download, download_raw, index
from src.application.interfaces import ProviderUnavailableError

from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Handles startup (setup database) and shutdown (close connections).
    """
    from src.infrastructure.services.turso_repository import TursoBookRepository
    repo = TursoBookRepository()
    app.state.turso_repo = repo
    
    # Startup logic
    if repo.client:
        print("🚀 [TURSO] Inicializando banco de dados...")
        await repo.setup()
        print("✅ [TURSO] Tabela formatted_books garantida.")
    
    yield # Separator between startup and shutdown
    
    # Shutdown logic
    if hasattr(app.state, "turso_repo"):
        await app.state.turso_repo.close()

app = FastAPI(
    title="BiblioCLI API", 
    description="Backend API to search, download and format eBooks for TTS Engines.",
    version="1.0",
    lifespan=lifespan
)



@app.exception_handler(ProviderUnavailableError)
async def provider_unavailable_exception_handler(request: Request, exc: ProviderUnavailableError):
    return JSONResponse(
        status_code=503,
        content={
            "error": "ProviderUnavailable",
            "message": str(exc),
            "provider": exc.provider_name
        },
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# API Routes
app.include_router(index.router)
app.include_router(search.router, prefix="/api/v1")
app.include_router(download.router, prefix="/api/v1")
app.include_router(download_raw.router, prefix="/api/v1")

# Static Assets
static_path = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)

app.mount("/static", StaticFiles(directory=static_path), name="static")


