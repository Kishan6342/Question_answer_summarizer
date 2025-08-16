from langchain_groq import ChatGroq
from src.config.settings import settings
from src.common.logger import get_logger

def get_groq_llm():
    """Initialize and return Groq LLM client"""
    logger = get_logger("GroqClient")
    
    try:
        llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.MODEL_NAME,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )
        logger.info(f"Groq LLM initialized with model: {settings.MODEL_NAME}")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize Groq LLM: {str(e)}")
        raise
