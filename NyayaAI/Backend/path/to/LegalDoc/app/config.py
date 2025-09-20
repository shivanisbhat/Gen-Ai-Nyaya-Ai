# from pydantic import BaseSettings
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATA_DIR: str = "./data"
    FAISS_INDEX_PATH: str = "./data/faiss.index"
    DB_PATH: str = "./data/metadata.db"

    # Google AI Studio (FREE)
    GOOGLE_API_KEY: str
    
    # Model settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Free local embeddings
    LLM_MODEL: str = "gemini-1.5-flash"  # Free Gemini model

    class Config:
        env_file = ".env"

settings = Settings()
