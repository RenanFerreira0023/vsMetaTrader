from pydantic import model_validator
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "MQL Robot Factory API"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Banco de Dados Config
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "1234"
    DB_NAME: str = "vsmetatrader"

    # Agora incluído na classe Settings:
    USE_GPU: bool = True
    DEVICE: str = "gpu"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    @model_validator(mode='after')
    def set_device(self):
        # Garante que DEVICE respeite USE_GPU caso um deles seja alterado no .env
        if not self.USE_GPU:
            self.DEVICE = "cpu"
        return self


    
    # Model Config
    MODEL_NAME: str = "deepseek-coder:6.7b-instruct-q4_K_M"
    MODEL_PATH: str = "./models"
    
    # RAG Config
    ROBOTS_PATH: str = "./robots"
    
    # Security Config
    ALLOWED_ORIGINS: List[str] = ["*"]
    TRUSTED_HOSTS: List[str] = ["*"]
    
    # Generative Config
    CONTEXT_SIZE: int = 16384  
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.1
    MAX_AGENT_ITERATIONS: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
