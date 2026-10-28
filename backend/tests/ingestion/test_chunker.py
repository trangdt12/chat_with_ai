import unicodedata

from app.ingestion.chunker import chunk_pages, split_blocks, split_sentences
from app.ingestion.pdf import is_scanned


def _sentences(n: int, prefix: str) -> str:
    return " ".join(f"{prefix} câu số {i} nói về điều khoản thanh toán của hợp đồng." for i in range(n))


def test_chunk_never_crosses_page():
    pages = [_sentences(80, "Trang một"), "", _sentences(80, "Trang ba")]
    drafts = chunk_pages(pages, max_chars=500)
    assert drafts
    for d in drafts:
        assert d.page_number in (1, 3)
        marker = "Trang một" if d.page_number == 1 else "Trang ba"
        other = "Trang ba" if d.page_number == 1 else "Trang một"
        assert marker in d.content and other not in d.content
    assert [d.chunk_index for d in drafts] == list(range(len(drafts)))


def test_chunk_max_len_and_overlap():
    drafts = chunk_pages([_sentences(200, "A")], max_chars=1800)
    assert len(drafts) > 1
    for prev, nxt in zip(drafts, drafts[1:], strict=False):
        assert len(prev.content) <= 1800
        last_sentence = split_sentences(prev.content)[-1]
        assert nxt.content.startswith(last_sentence)
    assert len(drafts[-1].content) <= 1800


def test_long_sentence_hard_split():
    sentence = " ".join(["từkhóa"] * 600)  # ~4.200 ký tự, không có dấu câu
    drafts = chunk_pages([sentence], max_chars=1800)
    assert len(drafts) >= 3
    for d in drafts:
        assert len(d.content) <= 1800
        assert not d.content.startswith(" ") and "từkhóa" in d.content
        assert all(w == "từkhóa" for w in d.content.split())  # cắt tại khoảng trắng, không cắt giữa từ


def test_split_sentences_keeps_numbers():
    assert split_sentences("Giá 1.000,5 triệu. Hạn 30 ngày.") == ["Giá 1.000,5 triệu.", "Hạn 30 ngày."]
    assert split_sentences("Phiên bản 3.2 ổn định; dùng tiếp\nDòng mới") == [
        "Phiên bản 3.2 ổn định;",
        "dùng tiếp",
        "Dòng mới",
    ]


def test_split_blocks_deterministic():
    text = _sentences(30, "B") + " " + " ".join(["dài"] * 200)
    first = split_blocks(text, 300)
    assert first == split_blocks(text, 300)
    assert all(0 < len(b) <= 300 for b in first)
    assert " ".join(first).replace(" ", "") == text.replace(" ", "")  # không mất chữ, không chồng lấn


def test_normalization_nfc_and_whitespace():
    decomposed = "Thời   hạn\n\n\nthanh toán"  # NFD + nhiều khoảng trắng, dòng trống
    [d] = chunk_pages([unicodedata.normalize("NFD", decomposed)])
    assert d.content == "Thời hạn thanh toán"
    assert unicodedata.is_normalized("NFC", d.content)


def test_is_scanned():
    full = "x" * 100
    assert is_scanned([""] * 8 + [full] * 2) is True
    assert is_scanned([""] * 7 + [full] * 3) is False
    assert is_scanned([]) is True
