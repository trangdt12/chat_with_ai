"""Đọc PDF và phát hiện lỗi: mật khẩu, hỏng, quá số trang, bản scan (ALG-01)."""

from pypdf import PasswordType, PdfReader

SCAN_MIN_CHARS = 30
SCAN_SPARSE_RATIO = 0.8


class PdfError(Exception):
    def __init__(self, code: str):  # encrypted | corrupt | too_many_pages | no_text
        super().__init__(code)
        self.code = code


def extract_pages(path: str, max_pages: int = 200) -> list[str]:
    try:
        reader = PdfReader(path)
    except Exception as e:
        raise PdfError("corrupt") from e

    if reader.is_encrypted:
        # PDF chỉ có owner password (mở được bằng mật khẩu rỗng) vẫn được nhận.
        try:
            ok = reader.decrypt("") != PasswordType.NOT_DECRYPTED
        except Exception:
            ok = False
        if not ok:
            raise PdfError("encrypted")

    try:
        count = len(reader.pages)
    except Exception as e:
        raise PdfError("corrupt") from e
    if count == 0:
        raise PdfError("corrupt")
    if count > max_pages:
        raise PdfError("too_many_pages")

    try:
        return [page.extract_text() or "" for page in reader.pages]
    except Exception as e:
        raise PdfError("corrupt") from e


def is_scanned(pages: list[str]) -> bool:
    """ALG-01: ≥ 80% số trang có < 30 ký tự → coi là bản scan."""
    if not pages:
        return True
    sparse = sum(1 for t in pages if len(t.strip()) < SCAN_MIN_CHARS)
    return sparse / len(pages) >= SCAN_SPARSE_RATIO
