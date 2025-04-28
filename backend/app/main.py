from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine
from app.models.invoice import Base
from datetime import datetime

# Veritabanı tablolarını oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for extracting data from invoice images",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API rotalarını ekle
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """
    Ana sayfa - API bilgilerini göster ve dokümantasyona yönlendir
    """
    return JSONResponse({
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "Fatura ve fiş görsellerinden veri çıkarma API'si",
        "endpoints": {
            "documentation": "/docs",
            "openapi_spec": f"{settings.API_V1_STR}/openapi.json",
            "health_check": "/health",
            "extract_invoice": f"{settings.API_V1_STR}/ocr/extract"
        },
        "status": "running"
    })


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_redirect():
    """
    Swagger UI'ya yönlendir
    """
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    """
    API sağlık kontrolü
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION
    }
