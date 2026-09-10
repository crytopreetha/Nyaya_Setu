"""
Local, offline embeddings so retrieval works with zero external API calls —
only the final explanation step needs an LLM key (see services/llm.py).
"""
from functools import lru_cache

import numpy as np


@lru_cache
def _get_model():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name="BAAI/bge-small-en-v1.5")


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _get_model()
    return [vec.tolist() for vec in model.embed(texts)]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr, b_arr = np.array(a), np.array(b)
    denom = (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)) or 1e-9
    return float(np.dot(a_arr, b_arr) / denom)
