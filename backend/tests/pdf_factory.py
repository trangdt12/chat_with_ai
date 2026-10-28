"""Sinh PDF nhỏ cho test (thay cho file mẫu trong tests/fixtures/pdf/).

`make_pdf(["trang 1", "trang 2"])` → PDF hợp lệ, mỗi trang vẽ chữ bằng font Helvetica chuẩn
(chỉ ký tự Latin-1; ký tự khác thành "?"), pypdf trích xuất lại được.
"""

import io
import textwrap

from pypdf import PdfReader, PdfWriter


def _escape(line: str) -> str:
    line = line.encode("latin-1", "replace").decode("latin-1")
    return line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _content_stream(text: str) -> bytes:
    lines = [ln for para in text.split("\n") for ln in (textwrap.wrap(para, 90) or [""])]
    ops = ["BT", "/F1 11 Tf", "14 TL", "50 800 Td"]
    for ln in lines:
        ops.append(f"({_escape(ln)}) Tj T*")
    ops.append("ET")
    return "\n".join(ops).encode("latin-1")


def make_pdf(pages: list[str]) -> bytes:
    objects: list[bytes] = []
    n = len(pages)
    page_ids = [4 + 2 * i for i in range(n)]
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    for i, text in enumerate(pages):
        content_id = page_ids[i] + 1
        objects.append(
            (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
            ).encode()
        )
        stream = _content_stream(text) if text else b""
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for num, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{num} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return out.getvalue()


def encrypt_pdf(data: bytes, user_password: str = "secret", owner_password: str = "owner") -> bytes:
    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(data)))
    writer.encrypt(user_password=user_password, owner_password=owner_password)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


CORRUPT_PDF = b"%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n this is not a pdf \n%%EOF\n"

DOCX_BYTES = b"PK\x03\x04" + b"\x00" * 64  # file .docx (zip) — sai magic bytes

SAMPLE_PAGES = [
    "Hop dong khung so HD-2024-017 giua Cong ty A va Cong ty B. Thoi han thanh toan la 30 ngay ke tu ngay "
    "nhan hoa don. Truong hop cham giao hang, thoi han thanh toan duoc gia han them 15 ngay.",
    "Phu luc 2. Bang gia dich vu nam 2024. Don gia trien khai la 1.000,5 trieu dong. Bao hanh 12 thang.",
]


def sample_pdf() -> bytes:
    return make_pdf(SAMPLE_PAGES)
