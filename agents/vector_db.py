"""
author: DeJongnick
name: vector_db.py
date: 11/10/2025 (creation)
"""

import json
import re
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from html import unescape
from sentence_transformers import SentenceTransformer


class VectorDBClient:
    """Client for querying the articles vector database."""
    
    def __init__(self, embeddings_path: str, metadata_path: str, raw_dir: Optional[str] = None, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the vector database client.
        
        Args:
            embeddings_path: Path to the embeddings.npy file
            metadata_path: Path to the metadata.jsonl file
            raw_dir: Path to the directory containing HTML files (optional, for loading text)
            model_name: Name of the sentence-transformers model to use
        """
        # Convert to Path objects (keep as relative paths)
        self.embeddings_path = Path(embeddings_path)
        self.metadata_path = Path(metadata_path)
        if raw_dir:
            self.raw_dir = Path(raw_dir)
        else:
            self.raw_dir = None
        self.model_name = model_name
        
        # Load embeddings and metadata
        self.embeddings = None
        self.metadata = []
        self.model = None
        self._load_data()
    
    def _load_data(self):
        """Load embeddings and metadata from files."""
        # Load embeddings
        if not self.embeddings_path.exists():
            raise FileNotFoundError(f"Embeddings file not found: {self.embeddings_path}")
        self.embeddings = np.load(self.embeddings_path)
        
        # Load metadata
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_path}")
        
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    self.metadata.append(json.loads(line))
        
        # Load model
        print(f"Loading model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print("Model loaded.")
        
        print(f"Loaded {len(self.embeddings)} embeddings and {len(self.metadata)} metadata entries")
    
    def search(self, query: str, top_k: int = 10, threshold: float = 0.0) -> List[Dict]:
        """
        Search for the most relevant articles for a query.
        
        Args:
            query: Search query (text)
            top_k: Number of results to return
            threshold: Minimum similarity threshold (0.0 = no threshold)
        
        Returns:
            List of dicts containing results with:
            - 'source': source file name
            - 'chunk_index': chunk index within the article
            - 'score': similarity score
            - 'metadata': full metadata for the chunk
        """
        if self.embeddings is None or len(self.embeddings) == 0:
            return []
        
        # Encode the query
        query_embedding = self.model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        query_embedding = query_embedding.reshape(1, -1)
        
        # Compute cosine similarity (embeddings are already normalized)
        similarities = np.dot(self.embeddings, query_embedding.T).flatten()
        
        # Get top_k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Build the results
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= threshold:
                result = {
                    'source': self.metadata[idx]['source'],
                    'chunk_index': self.metadata[idx]['chunk_index'],
                    'score': score,
                    'metadata': self.metadata[idx]
                }
                results.append(result)
        
        return results
    
    def get_article_chunks(self, source: str) -> List[Dict]:
        """
        Retrieve all chunks for a given article.
        
        Args:
            source: Source file name
        
        Returns:
            List of metadata dicts for all chunks in the article
        """
        return [meta for meta in self.metadata if meta['source'] == source]
    
    @staticmethod
    def _html_to_text(html: str) -> str:
        """Extracts text from an HTML file."""
        text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
        text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = unescape(text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    
    @staticmethod
    def _simple_tokenize(text: str) -> List[str]:
        """Tokenizes text into simple tokens."""
        text = text.lower()
        tokens = re.findall(r"[a-z0-9]+", text)
        return tokens
    
    @staticmethod
    def _chunk_tokens(tokens: List[str], chunk_size: int = 500, overlap: int = 50) -> List[List[str]]:
        """Splits tokens into chunks with overlap."""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be > 0")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be >= 0 and < chunk_size")

        chunks = []
        start = 0
        step = chunk_size - overlap
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunks.append(tokens[start:end])
            if end == len(tokens):
                break
            start += step
        return chunks
    
    def get_chunk_text(self, source: str, chunk_index: int) -> Optional[str]:
        """
        Retrieves the text of a specific chunk from the source HTML file.
        
        Args:
            source: Source file name
            chunk_index: Index of the chunk within the article
        
        Returns:
            The chunk's text or None if the file is not found
        """
        if self.raw_dir is None:
            return None
        
        html_file = self.raw_dir / source
        if not html_file.exists():
            return None
        
        try:
            html = html_file.read_text(encoding='utf-8', errors='ignore')
            text = self._html_to_text(html)
            tokens = self._simple_tokenize(text)
            token_chunks = self._chunk_tokens(tokens, chunk_size=500, overlap=50)
            
            if 0 <= chunk_index < len(token_chunks):
                return " ".join(token_chunks[chunk_index])
        except Exception as e:
            print(f"Error loading chunk text: {e}")
            return None
        
        return None