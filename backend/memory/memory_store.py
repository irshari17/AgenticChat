"""
In-memory vector-like store for context retrieval.
Stores text chunks with simple TF-IDF-like similarity for retrieval.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import math
import re
from collections import Counter
import uuid


class MemoryItem:
    """A single item in the memory store."""

    def __init__(self, content: str, metadata: Dict[str, Any] = None):
        self.id = str(uuid.uuid4())
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.tokens = self._tokenize(content)
        self.token_counts = Counter(self.tokens)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple whitespace + lowercase tokenization."""
        text = re.sub(r"[^\w\s]", " ", text.lower())
        return [t for t in text.split() if len(t) > 1]


class MemoryStore:
    """
    Simple in-memory store with TF-IDF-based retrieval.
    For production, replace with a proper vector DB (Chroma, Pinecone, etc.)
    """

    def __init__(self, max_items: int = 100):
        self.max_items = max_items
        self.items: List[MemoryItem] = []
        self._idf_cache: Dict[str, float] = {}
        self._cache_valid = False

    def add(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """Add a new item to the memory store. Returns the item ID."""
        item = MemoryItem(content=content, metadata=metadata)
        self.items.append(item)
        self._cache_valid = False

        # Evict oldest if over limit
        if len(self.items) > self.max_items:
            self.items = self.items[-self.max_items:]

        return item.id

    def _compute_idf(self):
        """Compute inverse document frequency for all tokens."""
        if self._cache_valid:
            return

        n_docs = len(self.items)
        if n_docs == 0:
            self._idf_cache = {}
            self._cache_valid = True
            return

        # Count how many docs contain each token
        doc_freq: Counter = Counter()
        for item in self.items:
            unique_tokens = set(item.tokens)
            for token in unique_tokens:
                doc_freq[token] += 1

        self._idf_cache = {
            token: math.log((n_docs + 1) / (freq + 1)) + 1
            for token, freq in doc_freq.items()
        }
        self._cache_valid = True

    def _tfidf_vector(self, token_counts: Counter) -> Dict[str, float]:
        """Compute TF-IDF vector for a token count dict."""
        total = sum(token_counts.values())
        if total == 0:
            return {}
        return {
            token: (count / total) * self._idf_cache.get(token, 1.0)
            for token, count in token_counts.items()
        }

    @staticmethod
    def _cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """Compute cosine similarity between two sparse vectors."""
        common_keys = set(vec_a.keys()) & set(vec_b.keys())
        if not common_keys:
            return 0.0

        dot = sum(vec_a[k] * vec_b[k] for k in common_keys)
        norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[MemoryItem, float]]:
        """
        Search for the most relevant items given a query string.
        Returns list of (MemoryItem, similarity_score) tuples.
        """
        if not self.items:
            return []

        self._compute_idf()

        query_item = MemoryItem(content=query)
        query_vec = self._tfidf_vector(query_item.token_counts)

        scored: List[Tuple[MemoryItem, float]] = []
        for item in self.items:
            item_vec = self._tfidf_vector(item.token_counts)
            score = self._cosine_similarity(query_vec, item_vec)
            scored.append((item, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def get_recent(self, n: int = 10) -> List[MemoryItem]:
        """Get the N most recent items."""
        return self.items[-n:]

    def clear(self):
        """Clear all items from the store."""
        self.items.clear()
        self._cache_valid = False

    def __len__(self) -> int:
        return len(self.items)
