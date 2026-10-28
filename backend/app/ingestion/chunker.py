"""ALG-02: chia văn bản theo trang thành đoạn ≤ max_chars. Python thuần, không I/O, tất định."""

import re
import unicodedata
from dataclasses import dataclass

# Tách sau . ! ? … ; khi theo sau là khoảng trắng, và tách ở xuống dòng.
# "1.000,5" hay "3.2" không có khoảng trắng sau dấu chấm nên không bị tách.
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?…;])[ \t]+|\n+")
_SPACES = re.compile(r"[ \t ​]+")


@dataclass(frozen=True)
class ChunkDraft:
    page_number: int  # 1-based
    chunk_index: int  # tăng liên tục trong cả tài liệu
    content: str  # ≤ chunk_max_chars


def normalize_page(text: str) -> str:
    """NFC, gộp khoảng trắng liên tiếp, bỏ dòng trống."""
    text = unicodedata.normalize("NFC", text)
    lines = (_SPACES.sub(" ", ln).strip() for ln in text.splitlines())
    return "\n".join(ln for ln in lines if ln)


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_BOUNDARY.split(text) if s and s.strip()]


def hard_split(sentence: str, max_chars: int) -> list[str]:
    """Cắt câu dài hơn max_chars tại khoảng trắng gần nhất (không có khoảng trắng thì cắt cứng)."""
    pieces: list[str] = []
    rest = sentence
    while len(rest) > max_chars:
        cut = rest.rfind(" ", 0, max_chars + 1)
        if cut <= 0:
            cut = max_chars
        pieces.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    if rest:
        pieces.append(rest)
    return pieces


def _units(text: str, max_chars: int) -> list[str]:
    return [p for s in split_sentences(text) for p in hard_split(s, max_chars)]


def _greedy(units: list[str], max_chars: int, overlap: bool) -> list[str]:
    groups: list[str] = []
    current: list[str] = []
    length = 0
    for unit in units:
        added = len(unit) + (1 if current else 0)
        if current and length + added > max_chars:
            groups.append(" ".join(current))
            carry = current[-1] if overlap else None
            if carry is not None and len(carry) + 1 + len(unit) <= max_chars:
                current, length = [carry], len(carry)
            else:
                current, length = [], 0
            added = len(unit) + (1 if current else 0)
        current.append(unit)
        length += added
    if current:
        groups.append(" ".join(current))
    return groups


def chunk_pages(pages: list[str], max_chars: int = 1800) -> list[ChunkDraft]:
    """Mỗi trang chia riêng (không đoạn nào chứa văn bản của 2 trang); đoạn sau chồng lấn 1 câu với đoạn trước."""
    drafts: list[ChunkDraft] = []
    for page_number, raw in enumerate(pages, start=1):
        text = normalize_page(raw)
        if not text:
            continue
        for content in _greedy(_units(text, max_chars), max_chars, overlap=True):
            drafts.append(ChunkDraft(page_number=page_number, chunk_index=len(drafts), content=content))
    return drafts


def split_blocks(text: str, max_chars: int = 300) -> list[str]:
    """Gom câu thành các khối ≤ max_chars (không chồng lấn). T-09 dùng lại để tạo khối con trong search_result."""
    return _greedy(_units(text, max_chars), max_chars, overlap=False)
