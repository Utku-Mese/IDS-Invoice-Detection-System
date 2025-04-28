from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Invoice Detection System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Geliştirme için SQLite kullanıyoruz
    DATABASE_URL: str = "sqlite:///./invoices.db"

    # CORS ayarları
    BACKEND_CORS_ORIGINS: list = ["*"]

    # Tesseract dil ayarı
    TESSERACT_LANG: str = "tur"

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
