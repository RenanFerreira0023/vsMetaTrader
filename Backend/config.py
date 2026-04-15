from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "DeepSeek-R1 API"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Model Config
    MODEL_NAME: str = "Llama-3.2-1B-Instruct-Q4_0.gguf"
    MODEL_PATH: str = "./models"
    
    # Security Config
    ALLOWED_ORIGINS: List[str] = ["*"]
    TRUSTED_HOSTS: List[str] = ["*"]
    
    # Generative Config
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.6

    class Config:
        env_file = ".env"

settings = Settings()
