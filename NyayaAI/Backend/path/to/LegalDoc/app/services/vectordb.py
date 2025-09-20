import faiss
import numpy as np
import os
import pickle
from typing import List
from app.config import settings

# Dimension for sentence-transformers 'all-MiniLM-L6-v2' is 384
INDEX_DIM = 384

class FaissIndex:
    def __init__(self, index_path: str = None):
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.index = None
        self.metadata = []
        self.load()

    def create(self):
        """Create a new FAISS index"""
        self.index = faiss.IndexFlatL2(INDEX_DIM)
        self.metadata = []
        print(f"✅ Created new FAISS index with dimension {INDEX_DIM}")

    def add(self, vectors: np.ndarray, metadatas: List[dict]):
        """Add vectors and metadata to the index"""
        if self.index is None:
            self.create()
        
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)
        
        if vectors.shape[1] != INDEX_DIM:
            raise ValueError(f"Vector dimension {vectors.shape[1]} doesn't match index dimension {INDEX_DIM}")
        
        self.index.add(vectors)
        self.metadata.extend(metadatas)

    def search(self, vector: np.ndarray, top_k: int = 5):
        """Search for similar vectors"""
        if self.index is None or self.index.ntotal == 0:
            return []
        
        if vector.ndim == 1:
            vector = vector.reshape(1, -1)
        
        if vector.shape[1] != INDEX_DIM:
            raise ValueError(f"Query vector dimension {vector.shape[1]} doesn't match index dimension {INDEX_DIM}")
        
        D, I = self.index.search(vector, min(top_k, self.index.ntotal))
        results = []
        
        for dist, idx in zip(D[0], I[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            md = dict(self.metadata[idx])
            md['score'] = float(dist)
            results.append(md)
        
        return results

    def save(self):
        """Save index and metadata to disk"""
        if self.index is None:
            return
        
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        
        meta_path = self.index_path + ".meta.pkl"
        with open(meta_path, "wb") as f:
            pickle.dump(self.metadata, f)
        
        print(f"💾 Saved FAISS index with {self.index.ntotal} vectors")

    def load(self):
        """Load index and metadata from disk"""
        if os.path.exists(self.index_path) and os.path.exists(self.index_path + ".meta.pkl"):
            try:
                self.index = faiss.read_index(self.index_path)
                meta_path = self.index_path + ".meta.pkl"
                with open(meta_path, "rb") as f:
                    self.metadata = pickle.load(f)
                print(f"📂 Loaded FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                print(f"⚠️ Error loading index, creating new one: {e}")
                self.create()
        else:
            print("📂 No existing index found, will create new one when needed")

# Singleton instance
faiss_index = FaissIndex()
