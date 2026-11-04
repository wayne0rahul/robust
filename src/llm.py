import os
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import settings

def get_llm(
    provider: Optional[str] = None,
    temperature: float = 0.5,
    max_tokens: int = 2048
) -> BaseChatModel:
    """
    Factory function returning a configured ChatModel.
    Supports Groq (default, ultra-fast) and Google Gemini (fallback/alternative).
    Both have free developer tiers.
    """
    selected_provider = (provider or settings.get_active_provider()).lower()
    
    if selected_provider == "groq":
        api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        if not api_key:
            # Check if Gemini / Google key is available as automatic fallback
            if settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
                selected_provider = "gemini"
            else:
                raise ValueError(
                    "GROQ_API_KEY is not set. Please set it in your .env file or environment, "
                    "or obtain a free key at https://console.groq.com."
                )
                
    if selected_provider == "groq":
        return ChatGroq(
            model=settings.GROQ_MODEL,
            groq_api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    elif selected_provider == "gemini":
        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            # Check if Groq key is available
            if settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", ""):
                return ChatGroq(
                    model=settings.GROQ_MODEL,
                    groq_api_key=settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", ""),
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                raise ValueError(
                    "GEMINI_API_KEY is not set. Please set it in your .env file or environment, "
                    "or obtain a free key at https://aistudio.google.com."
                )
                
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=api_key,
            temperature=temperature,
            max_output_tokens=max_tokens
        )
    
    else:
        raise ValueError(f"Unsupported LLM provider: '{selected_provider}'. Choose 'groq' or 'gemini'.")

