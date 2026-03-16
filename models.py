from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://blackbird:blackbird_secret@localhost:5432/blackbird"
    sync_database_url: str = "postgresql://blackbird:blackbird_secret@localhost:5432/blackbird"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # API
    api_key: str = "blackbird-alpha-key"
    debug: bool = True

    # Storage
    upload_dir: str = "./uploads"

    # YOLO model
    yolo_model: str = "yolov8n.pt"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Ensure upload dir exists
os.makedirs(settings.upload_dir, exist_ok=True)
