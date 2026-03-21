"""
Vector database and retrieval service using FAISS
Provides semantic search with K-NN similarity
"""
from typing import List, Dict, Tuple, Optional
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import pickle
import re


class FAISSIndex:
    """FAISS-based vector index for semantic search"""
    
    def __init__(self, embedding_dim: int, index_dir: str = "data/vector_index", use_compression: bool = True):
        """
        Initialize FAISS index
        
        Args:
            embedding_dim: Dimension of embeddings
            index_dir: Directory to store index
            use_compression: Use IVFFlat compression for better memory efficiency
        """
        self.embedding_dim = embedding_dim
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.index_dir / "faiss.idx"
        self.metadata_file = self.index_dir / "metadata.json"
        self.use_compression = use_compression
        
        self.index = None
        self.id_map = []  # Maps index position to candidate_id
        self.metadata = self._load_metadata()
        self._load_index(use_compression=use_compression)
    
    def _load_index(self, use_compression: bool = True):
        """Load FAISS index from disk with optional compression"""
        try:
            import faiss
            if self.index_file.exists():
                self.index = faiss.read_index(str(self.index_file))
                print(f"✓ Loaded FAISS index with {self.index.ntotal} vectors")
            else:
                if use_compression and self.embedding_dim >= 100:
                    # Use compressed index (IndexIVFFlat) for large embeddings
                    quantizer = faiss.IndexFlatL2(self.embedding_dim)
                    self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, nlist=100)
                    print(f"✓ Created compressed FAISS index with IVF (dimension: {self.embedding_dim})")
                else:
                    # Use full index for small embeddings
                    self.index = faiss.IndexFlatL2(self.embedding_dim)
                    print(f"✓ Created new FAISS index (dimension: {self.embedding_dim})")
        except ImportError:
            raise ImportError("faiss-cpu not installed. Run: pip install faiss-cpu")
    
    def add_embeddings(self, embeddings: np.ndarray, candidate_ids: List[str]):
        """
        Add embeddings to index
        
        Args:
            embeddings: numpy array of shape (n, embedding_dim)
            candidate_ids: List of candidate IDs corresponding to embeddings
        """
        import faiss
        
        # Ensure embeddings are float32
        embeddings = embeddings.astype(np.float32)
        
        # Train IVFFlat index on first batch if needed
        if self.use_compression and hasattr(self.index, 'is_trained') and not self.index.is_trained:
            training_size = min(len(embeddings), 256)  # Train on up to 256 vectors
            self.index.train(embeddings[:training_size])
        
        # Add to index
        self.index.add(embeddings)
        self.id_map.extend(candidate_ids)
        
        # Update metadata
        for i, cand_id in enumerate(candidate_ids):
            self.metadata["indexed_candidates"][cand_id] = {
                "index_pos": len(self.id_map) - len(candidate_ids) + i,
                "created_at": datetime.now().isoformat()
            }
        
        self._save_index()
        self._save_metadata()
        print(f"✓ Added {len(embeddings)} embeddings to index (total: {self.index.ntotal})")
    
    def search(self, query_embedding: np.ndarray, k: int = 10, 
              threshold: float = 0.0) -> List[Tuple[str, float]]:
        """
        Search for similar embeddings
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            threshold: Minimum similarity score (for L2: max distance)
            
        Returns:
            List of (candidate_id, similarity_score) tuples
        """
        if self.index.ntotal == 0:
            return []
        
        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
        
        # Train index if IVFFlat (needed after first batch of data)
        if hasattr(self.index, 'is_trained') and not self.index.is_trained:
            self.index.train(query_embedding)
        
        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx >= 0 and idx < len(self.id_map):  # Valid index
                # Convert L2 distance to similarity (1 / (1 + distance))
                similarity = 1.0 / (1.0 + distance)
                if similarity >= threshold:
                    results.append((self.id_map[idx], float(similarity)))
        
        return results
    
    def search_batch(self, embeddings: np.ndarray, k: int = 10) -> List[List[Tuple[str, float]]]:
        """
        Search with multiple queries
        
        Args:
            embeddings: Query embeddings of shape (n, embedding_dim)
            k: Number of results per query
            
        Returns:
            List of (candidate_id, similarity_score) tuples per query
        """
        embeddings = embeddings.astype(np.float32)
        distances, indices = self.index.search(embeddings, min(k, self.index.ntotal))
        
        results = []
        for dist_row, idx_row in zip(distances, indices):
            row_results = []
            for idx, distance in zip(idx_row, dist_row):
                if idx >= 0 and idx < len(self.id_map):
                    similarity = 1.0 / (1.0 + distance)
                    row_results.append((self.id_map[idx], float(similarity)))
            results.append(row_results)
        
        return results
    
    def _save_index(self):
        """Save FAISS index to disk"""
        import faiss
        faiss.write_index(self.index, str(self.index_file))
    
    def _load_metadata(self) -> Dict:
        """Load index metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            "created_at": datetime.now().isoformat(),
            "indexed_candidates": {}
        }
    
    def _save_metadata(self):
        """Save index metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def get_stats(self) -> Dict:
        """Get index statistics"""
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.embedding_dim,
            "indexed_candidates": len(self.metadata["indexed_candidates"]),
            "created_at": self.metadata.get("created_at")
        }


class BM25Retriever:
    """BM25-based keyword retrieval (simple implementation)"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 retriever
        
        Args:
            k1, b: BM25 parameters
        """
        self.k1 = k1
        self.b = b
        self.documents = {}  # candidate_id -> text
        self.inverted_index = {}  # term -> list of candidate_ids
    
    def index_documents(self, candidates: List[Dict]):
        """
        Index documents for keyword search
        
        Args:
            candidates: List of dicts with 'candidate_id' and 'raw_text'
        """
        for cand in candidates:
            cand_id = cand['candidate_id']
            text = cand.get('raw_text', '')
            self.documents[cand_id] = text
            
            # Tokenize and index
            tokens = self._tokenize(text)
            for token in set(tokens):
                if token not in self.inverted_index:
                    self.inverted_index[token] = []
                self.inverted_index[token].append(cand_id)
        
        print(f"✓ Indexed {len(self.documents)} documents for keyword search")
    
    def search(self, query: str, k: int = 10) -> List[Tuple[str, float]]:
        """
        Search documents using keyword matching
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of (candidate_id, score) tuples
        """
        query_tokens = self._tokenize(query)
        scores = {}
        
        for token in query_tokens:
            if token in self.inverted_index:
                for cand_id in self.inverted_index[token]:
                    if cand_id not in scores:
                        scores[cand_id] = 0.0
                    scores[cand_id] += 1.0
        
        # Sort and return top-k
        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        return results
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        # Split on whitespace
        tokens = text.split()
        # Filter short tokens
        tokens = [t for t in tokens if len(t) > 2]
        return tokens


class HybridRetriever:
    """Hybrid retrieval combining semantic and keyword search"""
    
    def __init__(self, embedding_service, embedding_dim: int = 384):
        """
        Initialize hybrid retriever
        
        Args:
            embedding_service: EmbeddingService instance
            embedding_dim: Dimension of embeddings
        """
        self.embedding_service = embedding_service
        self.faiss_index = FAISSIndex(embedding_dim)
        self.bm25_retriever = BM25Retriever()
        self.candidates = {}  # Cache candidate metadata
    
    def index_candidates(self, candidates: List[Dict]):
        """
        Index candidates for hybrid search
        
        Args:
            candidates: List of candidate dicts with 'candidate_id' and 'raw_text'
        """
        # Cache candidates
        for cand in candidates:
            self.candidates[cand['candidate_id']] = cand
        
        # Index for keyword search
        self.bm25_retriever.index_documents(candidates)
        
        # Generate embeddings and index
        self.embedding_service.cache_embeddings(candidates)
        
        # Extract embeddings for already-indexed candidates
        embeddings = []
        ids = []
        for cand in candidates:
            cand_id = cand['candidate_id']
            if cand_id in self.embedding_service.embeddings_cache:
                embeddings.append(self.embedding_service.embeddings_cache[cand_id])
                ids.append(cand_id)
        
        if embeddings:
            embeddings = np.array(embeddings)
            self.faiss_index.add_embeddings(embeddings, ids)
    
    def search(self, query: str, k: int = 10, 
              semantic_weight: float = 0.6) -> List[Dict]:
        """
        Hybrid search combining semantic and keyword results
        
        Args:
            query: Search query
            k: Number of results
            semantic_weight: Weight for semantic results (0-1)
            
        Returns:
            List of result dicts with candidate info and scores
        """
        keyword_weight = 1.0 - semantic_weight
        
        # Semantic search
        query_embedding = self.embedding_service.embed_text(query)
        semantic_results = self.faiss_index.search(query_embedding, k=k*2)
        semantic_scores = {cid: score for cid, score in semantic_results}
        
        # Keyword search
        keyword_results = self.bm25_retriever.search(query, k=k*2)
        # Normalize keyword scores to 0-1
        if keyword_results:
            max_score = max(score for _, score in keyword_results)
            keyword_scores = {cid: (score / max_score) for cid, score in keyword_results}
        else:
            keyword_scores = {}
        
        # Combine scores
        combined_scores = {}
        all_ids = set(semantic_scores.keys()) | set(keyword_scores.keys())
        
        for cand_id in all_ids:
            s_score = semantic_scores.get(cand_id, 0.0)
            k_score = keyword_scores.get(cand_id, 0.0)
            combined_scores[cand_id] = semantic_weight * s_score + keyword_weight * k_score
        
        # Sort and format results
        sorted_ids = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:k]
        
        results = []
        for cand_id, score in sorted_ids:
            cand = self.candidates.get(cand_id, {})
            results.append({
                "candidate_id": cand_id,
                "score": float(score),
                "semantic_score": float(semantic_scores.get(cand_id, 0.0)),
                "keyword_score": float(keyword_scores.get(cand_id, 0.0)),
                "name": cand.get("name"),
                "skills": cand.get("skills", [])[:5]
            })
        
        return results
    
    def get_stats(self) -> Dict:
        """Get retrieval system statistics"""
        return {
            "vector_index": self.faiss_index.get_stats(),
            "keyword_index": {
                "documents": len(self.bm25_retriever.documents),
                "terms": len(self.bm25_retriever.inverted_index)
            },
            "cached_candidates": len(self.candidates)
        }


# Test
if __name__ == "__main__":
    # Test FAISS
    print("Testing FAISS Index...")
    index = FAISSIndex(embedding_dim=384)
    
    embeddings = np.random.randn(5, 384).astype(np.float32)
    candidate_ids = [f"cand_{i}" for i in range(5)]
    index.add_embeddings(embeddings, candidate_ids)
    
    query = embeddings[0]
    results = index.search(query, k=3)
    print(f"Search results: {results}")
    
    # Test BM25
    print("\nTesting BM25...")
    retriever = BM25Retriever()
    docs = [
        {"candidate_id": "c1", "raw_text": "Python developer with 5 years experience"},
        {"candidate_id": "c2", "raw_text": "Java software engineer expert"},
    ]
    retriever.index_documents(docs)
    results = retriever.search("Python developer", k=2)
    print(f"BM25 results: {results}")
