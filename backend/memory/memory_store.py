"""
TF-IDF-based in-memory vector store for context retrieval.
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import math
import re
from collections import Counter
import uuid
import logging

logger = logging.getLogger("memory.store")


class MemoryItem:
    def __init__(self, content: str, metadata: Dict[str, Any] = None, category: str = "general"):
        self.id = str(uuid.uuid4())
        self.content = content
        self.metadata = metadata or {}
        self.category = category
        self.timestamp = datetime.utcnow()
        self.tokens = self._tokenize(content)
        self.token_counts = Counter(self.tokens)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        text = re.sub(r"[^\w\s]", " ", text.lower())
        return [t for t in text.split() if len(t) > 1]


class MemoryStore:
    """TF-IDF-based memory store for semantic retrieval."""

    def __init__(self, max_items: int = 200):
        self.max_items = max_items
        self.items: List[MemoryItem] = []
        self._idf_cache: Dict[str, float] = {}
        self._cache_valid = False

    def add(self, content: str, metadata: Dict[str, Any] = None, category: str = "general") -> str:
        item = MemoryItem(content=content, metadata=metadata, category=category)
        self.items.append(item)
        self._cache_valid = False
        if len(self.items) > self.max_items:
            self.items = self.items[-self.max_items:]
        logger.debug(f"Memory added: {content[:80]}... (category={category})")
        return item.id

    def _compute_idf(self):
        if self._cache_valid:
            return
        n = len(self.items)
        if n == 0:
            self._idf_cache = {}
            self._cache_valid = True
            return
        doc_freq: Counter = Counter()
        for item in self.items:
            for token in set(item.tokens):
                doc_freq[token] += 1
        self._idf_cache = {
            t: math.log((n + 1) / (f + 1)) + 1
            for t, f in doc_freq.items()
        }
        self._cache_valid = True

    def _tfidf(self, counts: Counter) -> Dict[str, float]:
        total = sum(counts.values())
        if total == 0:
            return {}
        return {t: (c / total) * self._idf_cache.get(t, 1.0) for t, c in counts.items()}

    @staticmethod
    def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
        common = set(a) & set(b)
        if not common:
            return 0.0
        dot = sum(a[k] * b[k] for k in common)
        na = math.sqrt(sum(v ** 2 for v in a.values()))
        nb = math.sqrt(sum(v ** 2 for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    def search(self, query: str, top_k: int = 5, category: Optional[str] = None) -> List[Tuple[MemoryItem, float]]:
        if not self.items:
            return []
        self._compute_idf()
        q = MemoryItem(content=query)
        qv = self._tfidf(q.token_counts)
        scored = []
        for item in self.items:
            if category and item.category != category:
                continue
            iv = self._tfidf(item.token_counts)
            s = self._cosine(qv, iv)
            scored.append((item, s))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def get_recent(self, n: int = 10, category: Optional[str] = None) -> List[MemoryItem]:
        items = self.items if not category else [i for i in self.items if i.category == category]
        return items[-n:]

    def clear(self):
        self.items.clear()
        self._cache_valid = False

    def __len__(self):
        return len(self.items)
