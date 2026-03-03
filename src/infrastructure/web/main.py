from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from src.infrastructure.web.routes import books

app = FastAPI(
    title="BiblioCLI API", 
    description="Backend API to search, download and format eBooks for TTS Engines.",
    version="1.0"
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(books.router, prefix="/api/v1")

