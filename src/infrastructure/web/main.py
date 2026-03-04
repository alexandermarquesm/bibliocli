from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from src.infrastructure.web.routes import search, download, download_raw, index

app = FastAPI(
    title="BiblioCLI API", 
    description="Backend API to search, download and format eBooks for TTS Engines.",
    version="1.0"
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


