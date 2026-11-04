import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root if present
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

class Settings:
    # Providers: 'groq' or 'gemini'
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq").lower()
    
    # Groq Settings (openai/gpt-oss-20b avoids the 8k TPM limit of 120b)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    
    # Gemini / Google Settings (accepts both GEMINI_API_KEY and GOOGLE_API_KEY)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # Search Settings
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    
    # LangSmith / LangChain Settings
    LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "content-creation-system")

    @classmethod
    def get_active_provider(cls) -> str:
        """Determines the active provider based on availability and preference."""
        if cls.LLM_PROVIDER == "groq" and cls.GROQ_API_KEY:
            return "groq"
        if cls.LLM_PROVIDER == "gemini" and cls.GEMINI_API_KEY:
            return "gemini"
        
        # Automatic fallback if preferred provider key is missing
        if cls.GROQ_API_KEY:
            return "groq"
        if cls.GEMINI_API_KEY:
            return "gemini"
            
        return cls.LLM_PROVIDER

settings = Settings()

