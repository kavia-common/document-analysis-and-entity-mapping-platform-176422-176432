from PIL import Image

from src.services.parsing import parse_file_to_text

def test_parse_txt_plain(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("Hello CloudApp in USA")
    text, meta = parse_file_to_text(str(f))
    assert "CloudApp" in text
    assert meta["source"] == "plain"

def test_parse_image_ocr_fallback(tmp_path, monkeypatch):
    # Create small image with red
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    f = tmp_path / "img.jpg"
    img.save(f, format="JPEG")

    # Force OCR to return empty string
    from src.services import ocr as ocr_mod
    monkeypatch.setattr(ocr_mod, "ocr_image", lambda image: "")
    text, meta = parse_file_to_text(str(f))
    assert text == ""  # fallback empty text acceptable
    assert meta["source"] == "image"

def test_parse_xlsx(tmp_path, tiny_xlsx_file):
    text, meta = parse_file_to_text(str(tiny_xlsx_file))
    assert "Sheet1" in text
    assert meta["source"] == "xlsx"

def test_parse_pdf_handles_minimal_bytes(tmp_path):
    f = tmp_path / "a.pdf"
    # Minimal PDF with header/footer. pdfminer may return empty string; ensure no crash.
    f.write_bytes(b"%PDF-1.4\n%%EOF\n")
    text, meta = parse_file_to_text(str(f))
    assert isinstance(text, str)
    assert meta["suffix"] == ".pdf"
