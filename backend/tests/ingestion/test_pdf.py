import pytest

from app.ingestion.pdf import PdfError, extract_pages
from tests.pdf_factory import CORRUPT_PDF, SAMPLE_PAGES, encrypt_pdf, make_pdf, sample_pdf


def _write(tmp_path, data: bytes) -> str:
    path = tmp_path / "f.pdf"
    path.write_bytes(data)
    return str(path)


def test_extract_text_pages(tmp_path):
    pages = extract_pages(_write(tmp_path, sample_pdf()))
    assert len(pages) == len(SAMPLE_PAGES)
    assert "HD-2024-017" in pages[0]
    assert "1.000,5" in pages[1]


@pytest.mark.parametrize(
    ("data", "code"),
    [
        (encrypt_pdf(sample_pdf()), "encrypted"),
        (CORRUPT_PDF, "corrupt"),
        (make_pdf([""] * 201), "too_many_pages"),
    ],
    ids=["encrypted", "corrupt", "too_many_pages"],
)
def test_pdf_errors(tmp_path, data, code):
    with pytest.raises(PdfError) as exc:
        extract_pages(_write(tmp_path, data), max_pages=200)
    assert exc.value.code == code


def test_owner_password_only_is_accepted(tmp_path):
    data = encrypt_pdf(sample_pdf(), user_password="", owner_password="owner")
    assert len(extract_pages(_write(tmp_path, data))) == len(SAMPLE_PAGES)
