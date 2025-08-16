import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    MODEL_NAME: str = "llama3-70b-8192"
    TEMPERATURE: float = 0.3
    MAX_RETRIES: int = 3
    MAX_TOKENS: int = 4000
    
    class Config:
        env_file = ".env"

settings = Settings()
