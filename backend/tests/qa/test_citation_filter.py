import uuid

import pytest

from app.qa.citation_filter import CitationFilter, SourceRef, is_connective
from app.qa.llm import RawCitation, TextBlock

S0 = SourceRef(uuid.uuid4(), uuid.uuid4(), "HopDongKhung.pdf", 14)
S1 = SourceRef(uuid.uuid4(), uuid.uuid4(), "PhuLuc2.pdf", 3)


def cited(text: str, *indexes: int, cited_text: str = "đoạn trích") -> TextBlock:
    return TextBlock(text, tuple(RawCitation(i, cited_text) for i in indexes))


def plain(text: str) -> TextBlock:
    return TextBlock(text, ())


def run(blocks: list[TextBlock]):
    f = CitationFilter([S0, S1])
    emitted = [span for b in blocks for span in f.accept(b)]
    return f, emitted, f.finalize()


def test_cited_block_emitted_immediately():
    f = CitationFilter([S0, S1])
    spans = f.accept(cited("Thời hạn thanh toán là 30 ngày", 0))
    assert len(spans) == 1
    assert spans[0].citations[0].idx == 1
    assert spans[0].citations[0].filename == "HopDongKhung.pdf" and spans[0].citations[0].page == 14


def test_uncited_trailing_block_dropped():
    _, emitted, res = run([cited("Thời hạn thanh toán là 30 ngày", 0), plain(" Đây là mức phổ biến trong ngành")])
    assert [s.text for s in emitted] == ["Thời hạn thanh toán là 30 ngày"]
    assert res.answer_type == "answered"
    assert res.answer_text == "Thời hạn thanh toán là 30 ngày"


def test_uncited_leading_block_dropped():
    _, emitted, res = run([plain("Theo kinh nghiệm chung, "), cited("Thời hạn là 30 ngày", 0)])
    assert [s.text for s in emitted] == ["Thời hạn là 30 ngày"]
    assert res.answer_type == "answered"


def test_connective_between_cited_kept():
    _, emitted, _ = run([cited("A", 0), plain("Ngoài ra, "), cited("B", 1)])
    assert [(s.text, [c.idx for c in s.citations]) for s in emitted] == [("A", [1]), ("Ngoài ra, ", []), ("B", [2])]


def test_non_connective_between_dropped():
    _, emitted, _ = run([cited("A", 0), plain("Giá trị khác là 50 triệu"), cited("B", 1)])
    assert [s.text for s in emitted] == ["A", "B"]


def test_two_conflicting_values_both_shown():
    _, emitted, res = run([cited("HopDongKhung nêu 30 ngày", 0), plain("; "), cited("PhuLuc2 nêu 45 ngày", 1)])
    assert len([s for s in emitted if s.citations]) == 2
    assert {c.filename for c in res.citations} == {"HopDongKhung.pdf", "PhuLuc2.pdf"}


def test_all_uncited_is_not_found():
    _, emitted, res = run([plain("Thời hạn thường là 30 ngày."), plain(" Đây là mức phổ biến.")])
    assert emitted == []
    assert (res.answer_type, res.answer_text, res.citations) == ("not_found", "", ())


def test_marker_only_is_not_found():
    _, emitted, res = run([plain("[KHONG_TIM_THAY]")])
    assert emitted == [] and res.answer_type == "not_found"


def test_marker_in_sentence():
    _, emitted, res = run([plain("Rất tiếc: [KHONG_TIM_THAY]."), cited("Thời hạn 30 ngày", 0)])
    assert emitted == [] and res.answer_type == "not_found" and res.citations == ()


def test_clarify_with_citations():
    _, emitted, res = run([cited("[CAN_LAM_RO] Với dự án A là 30 ngày", 0), cited("; dự án B là 45 ngày", 1)])
    assert res.answer_type == "clarification"
    assert "[CAN_LAM_RO]" not in res.answer_text
    assert emitted[0].text == "Với dự án A là 30 ngày"


def test_clarify_without_citations_late_spans():
    _, emitted, res = run([plain("[CAN_LAM_RO] Bạn muốn hỏi hợp đồng nào: A hay B?")])
    assert emitted == []
    assert res.answer_type == "clarification"
    assert [s.text for s in res.late_spans] == ["Bạn muốn hỏi hợp đồng nào: A hay B?"]


def test_same_chunk_same_idx():
    f = CitationFilter([S0, S1])
    a = f.accept(cited("A", 0))[0].citations[0]
    b = f.accept(cited("B", 0))[0].citations[0]
    assert (a.idx, a.citation_id) == (b.idx, b.citation_id)


def test_out_of_range_index_ignored():
    _, emitted, res = run([cited("Thời hạn 30 ngày", 99)])
    assert emitted == [] and res.answer_type == "not_found"


def test_snippet_max_300():
    _, _, res = run([cited("A", 0, cited_text="x" * 1000)])
    assert len(res.citations[0].snippet) == 300


def test_snapshot_only_emitted():
    f = CitationFilter([S0, S1])
    f.accept(cited("Phần đã hiện", 0))
    f.accept(plain(" phần đang giữ chưa hiện"))
    text, citations = f.snapshot()
    assert text == "Phần đã hiện"
    assert [c.idx for c in citations] == [1]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Ngoài ra, ", True),
        ("\n- ", True),
        ("   ", True),
        ("trong vòng 30 ngày", False),
        ("Giá trị khác là 50 triệu", False),
        ("một hai ba bốn năm sáu bảy tám chín mười mười một mười hai mười ba", False),
        ("theo Công Ty Cổ Phần Alpha", False),
    ],
)
def test_is_connective_cases(text, expected):
    assert is_connective(text) is expected
