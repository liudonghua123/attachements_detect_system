from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Remote PostgreSQL Database Configuration
    REMOTE_DB_HOST: Optional[str] = None
    REMOTE_DB_PORT: int = 5432
    REMOTE_DB_NAME: Optional[str] = None
    REMOTE_DB_USER: Optional[str] = None
    REMOTE_DB_PASSWORD: Optional[str] = None
    
    # Local Database Configuration
    LOCAL_DB_TYPE: str = "sqlite"  # Options: sqlite, mysql, postgresql
    LOCAL_DB_HOST: Optional[str] = None
    LOCAL_DB_PORT: Optional[int] = None
    LOCAL_DB_NAME: Optional[str] = None
    LOCAL_DB_USER: Optional[str] = None
    LOCAL_DB_PASSWORD: Optional[str] = None
    LOCAL_DB_PATH: str = "./local_attachments.db"  # For SQLite
    
    # Cache Configuration
    ATTACHMENT_CACHE_DIR: str = "./attachments_cache"
    
    # OCR Engine Configuration ('paddle' or 'tesseract')
    OCR_ENGINE: str = "paddle"
    
    # PaddleOCR Configuration
    PADDLE_USE_GPU: bool = False
    
    # OpenAI API Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    MODEL: str = "gpt-4"
    PROMPTS: str = "Please analyze this content and identify any sensitive information like ID card numbers or phone numbers."

    # Attachment Base URL Configuration
    ATTACHMENT_DEFAULT_BASE_URL: str = "http://www.ynu.edu.cn"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()