from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from src.infrastructure.web.routes import books

app = FastAPI(
    title="BiblioCLI API", 
    description="Backend API to search, download and format eBooks for TTS Engines.",
    version="1.0"
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(books.router, prefix="/api/v1")

# Frontend
static_path = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(static_path, "index.html"))

app.mount("/static", StaticFiles(directory=static_path), name="static")


