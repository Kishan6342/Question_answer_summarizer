import streamlit as st
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    MODEL_NAME: str = "llama3-70b-8192"
    TEMPERATURE: float = 0.3
    MAX_RETRIES: int = 3
    MAX_TOKENS: int = 4000
    
    @property
    def GROQ_API_KEY(self) -> str:
        return st.secrets["GROQ_API_KEY"]

settings = Settings()

