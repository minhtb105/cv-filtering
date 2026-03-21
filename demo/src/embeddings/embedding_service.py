"""
Embedding service: Generate and manage embeddings for CVs
Uses sentence-transformers for local embedding generation (no API calls)
"""
from typing import List, Optional, Dict
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import pickle


class EmbeddingService:
    """Generate and cache embeddings using sentence-transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: str = "data/embeddings"):
        """
        Initialize embedding service
        
        Args:
            model_name: sentence-transformers model to use
            cache_dir: directory to cache embeddings and metadata
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "embeddings_metadata.json"
        self.embeddings_file = self.cache_dir / "embeddings.pkl"
        
        # Load or create metadata
        self.metadata = self._load_metadata()
        self.embeddings_cache = self._load_embeddings_cache()
        
        # Lazy load model
        self._model = None
    
    @property
    def model(self):
        """Lazy load the model on first use"""
        if self._model is None:
            print(f"Loading embedding model: {self.model_name}")
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
        return self._model
    
    def embed_text(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
            normalize: Whether to normalize the embedding
            
        Returns:
            numpy array of shape (embedding_dim,)
        """
        # Truncate very long texts
        text = text[:512]  # sentence-transformers typically works best with <512 tokens
        
        embedding = self.model.encode([text], convert_to_numpy=True)[0]
        
        if normalize:
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        return embedding
    
    def embed_batch(self, texts: List[str], batch_size: int = 64, 
                   normalize: bool = True) -> np.ndarray:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding
            normalize: Whether to normalize embeddings
            
        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        # Truncate texts
        texts = [t[:512] for t in texts]
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        if normalize:
            embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
        
        return embeddings
    
    def _load_metadata(self) -> Dict:
        """Load embedding metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            "model": self.model_name,
            "created_at": datetime.now().isoformat(),
            "embeddings": {}
        }
    
    def _save_metadata(self):
        """Save embedding metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _load_embeddings_cache(self) -> Dict[str, np.ndarray]:
        """Load cached embeddings"""
        if self.embeddings_file.exists():
            with open(self.embeddings_file, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def _save_embeddings_cache(self):
        """Save embeddings cache"""
        with open(self.embeddings_file, 'wb') as f:
            pickle.dump(self.embeddings_cache, f)
    
    def get_embedding(self, candidate_id: str, text: str, 
                     use_cache: bool = True) -> np.ndarray:
        """
        Get embedding for a candidate, using cache if available
        
        Args:
            candidate_id: Unique candidate identifier
            text: Raw CV text
            use_cache: Whether to use cached embedding if available
            
        Returns:
            numpy array embedding
        """
        if use_cache and candidate_id in self.embeddings_cache:
            return self.embeddings_cache[candidate_id]
        
        embedding = self.embed_text(text)
        self.embeddings_cache[candidate_id] = embedding
        self.metadata["embeddings"][candidate_id] = {
            "created_at": datetime.now().isoformat(),
            "model": self.model_name
        }
        
        return embedding
    
    def cache_embeddings(self, candidates: List[Dict]):
        """
        Cache embeddings for multiple candidates
        
        Args:
            candidates: List of dicts with 'candidate_id' and 'raw_text' keys
        """
        to_embed = []
        ids_to_embed = []
        
        for cand in candidates:
            cand_id = cand.get('candidate_id')
            if cand_id not in self.embeddings_cache:
                to_embed.append(cand.get('raw_text', ''))
                ids_to_embed.append(cand_id)
        
        if to_embed:
            print(f"Embedding {len(to_embed)} new candidates...")
            embeddings = self.embed_batch(to_embed)
            
            for cand_id, embedding in zip(ids_to_embed, embeddings):
                self.embeddings_cache[cand_id] = embedding
                self.metadata["embeddings"][cand_id] = {
                    "created_at": datetime.now().isoformat(),
                    "model": self.model_name
                }
            
            self._save_embeddings_cache()
            self._save_metadata()
            print(f"✓ Cached {len(to_embed)} embeddings")
    
    def get_embedding_dim(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()
    
    def clear_cache(self):
        """Clear all cached embeddings"""
        self.embeddings_cache = {}
        self.metadata["embeddings"] = {}
        if self.embeddings_file.exists():
            self.embeddings_file.unlink()
        if self.metadata_file.exists():
            self.metadata_file.unlink()


# Test
if __name__ == "__main__":
    service = EmbeddingService()
    
    # Test single embedding
    text1 = "Python developer with 5 years of experience in web development"
    emb1 = service.embed_text(text1)
    print(f"Embedding shape: {emb1.shape}")
    
    # Test batch embedding
    texts = [text1, "Java software engineer", "Data scientist with ML expertise"]
    embeddings = service.embed_batch(texts)
    print(f"Batch embeddings shape: {embeddings.shape}")
    
    # Test similarity
    similarity = np.dot(embeddings[0], embeddings[1])
    print(f"Similarity between text 1 and 2: {similarity:.4f}")
