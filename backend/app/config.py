from typing import Optional
import json
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AI Knowledge Hub"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./data/knowledge.db"
    SECRET_KEY: str = "ai-knowledge-hub-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list = ["*"]
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    EMBEDDING_BATCH_SIZE: int = 10
    EMBEDDING_TIMEOUT: int = 30
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_API_URL: str = ""
    EMBEDDING_RETRY: int = 3
    MCP_SERVER_NAME: str = "ai-knowledge-hub"
    MCP_SERVER_DESCRIPTION: str = "MCP Server for AI Knowledge Hub"
    MCP_SERVER_VERSION: str = "1.0.0"
    UPLOAD_DIR: str = "./data/uploads"
    BACKUP_DIR: str = "./data/backups"
    GRAPH_MAX_NODES_PER_LOAD: int = 200
    GRAPH_EXPAND_DEPTH: int = 2

    class Config:
        env_file = ".env"

settings = Settings()