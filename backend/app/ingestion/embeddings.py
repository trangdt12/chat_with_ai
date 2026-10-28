"""Embedding: bge-m3 chạy local (1024 chiều). Hàm chạy đồng bộ trên CPU — gọi qua asyncio.to_thread."""

import hashlib
import math
import re
import unicodedata
from functools import lru_cache
from typing import Protocol

from app.config import get_settings
from app.models import EMBED_DIM


class EmbedderProtocol(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class Embedder:
    def __init__(self, model_name: str):
        # Import muộn: pytest và chế độ EMBED_FAKE không cần tải torch.
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)  # cache ở HF_HOME=/models

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, batch_size=32, normalize_embeddings=True, convert_to_numpy=True)
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    return "".join(ch for ch in text if not unicodedata.combining(ch))


class FakeEmbedder:
    """Embedding giả cho pytest và e2e: túi từ (bỏ dấu, chữ thường) băm vào 1024 chiều, đã chuẩn hóa.

    Tất định, không cần model; câu có chung từ thì cosine cao, câu không liên quan thì cosine ≈ 0.
    """

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    @staticmethod
    def _embed(text: str) -> list[float]:
        vec = [0.0] * EMBED_DIM
        for token in re.findall(r"\w+", _fold(text)):
            h = int.from_bytes(hashlib.sha1(token.encode()).digest()[:4], "big")
            vec[h % EMBED_DIM] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            vec[0] = 1.0
            return vec
        return [v / norm for v in vec]


@lru_cache
def get_embedder() -> EmbedderProtocol:
    settings = get_settings()
    return FakeEmbedder() if settings.embed_fake else Embedder(settings.embed_model)


def embedding_text(filename: str, page: int, content: str) -> str:
    """Tiền tố chỉ dùng để tạo embedding, không lưu vào chunks.content."""
    return f"{filename} · trang {page}\n{content}"
