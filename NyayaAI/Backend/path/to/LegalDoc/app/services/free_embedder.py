import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Load the free sentence-transformers model
try:
    _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    print(f"✅ Free embedding model loaded: {settings.EMBEDDING_MODEL}")
except Exception as e:
    logger.error(f"Error loading embedding model: {e}")
    _model = None

def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Generate embeddings using free sentence-transformers
    texts: list[str] -> returns np.ndarray (n, 384)
    """
    if _model is None:
        raise RuntimeError("Embedding model not loaded")
        
    if not texts:
        return np.array([]).reshape(0, 384)  # MiniLM dimension is 384
    
    try:
        embs = _model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        result = embs.astype('float32')
        print(f"✅ Generated {len(texts)} embeddings, shape: {result.shape}")
        return result
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise
