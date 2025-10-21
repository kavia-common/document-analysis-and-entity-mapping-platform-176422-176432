from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# Third-party libraries
from pdfminer.high_level import extract_text
from docx import Document as DocxDocument
from pptx import Presentation
import pandas as pd


@dataclass
class ParsedFile:
    """Container for parsed file results and metadata."""
    filename: str
    content_type: str
    size_bytes: int
    file_type: str  # pdf, docx, pptx, csv, xlsx, other
    metric_label: str  # Pages, Paragraphs, Slides, Rows, Sheets
    metric_value: int
    text_excerpt: str = ""
    tables: List[Tuple[str, pd.DataFrame]] = field(default_factory=list)  # (sheet_name, df)
    parser_used: str = ""
    error: Optional[str] = None


# PUBLIC_INTERFACE
def parse_file(filename: str, content_type: str, data: bytes) -> ParsedFile:
    """Parse a single uploaded file and extract structured content and metrics.

    - Detects file type by extension.
    - Uses appropriate parser for pdf/docx/pptx/csv/xlsx.
    - On failure, captures error and returns a ParsedFile with error set.
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    size_bytes = len(data)

    try:
        if ext == "pdf":
            text = extract_text(io.BytesIO(data)) or ""
            pages = text.count("\f") + 1 if text else 0
            excerpt = text[:10000]
            return ParsedFile(
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
                file_type="pdf",
                metric_label="Pages",
                metric_value=pages,
                text_excerpt=excerpt,
                parser_used="pdfminer.six",
            )
        elif ext == "docx":
            doc = DocxDocument(io.BytesIO(data))
            paragraphs = [p.text for p in doc.paragraphs if p.text]
            text = "\n".join(paragraphs)
            excerpt = text[:10000]
            return ParsedFile(
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
                file_type="docx",
                metric_label="Paragraphs",
                metric_value=len(paragraphs),
                text_excerpt=excerpt,
                parser_used="python-docx",
            )
        elif ext == "pptx":
            prs = Presentation(io.BytesIO(data))
            slides_text: List[str] = []
            for slide in prs.slides:
                parts: List[str] = []
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        parts.append(shape.text)
                slides_text.append("\n".join(parts))
            text = "\n\n--- Slide Break ---\n\n".join(slides_text)
            excerpt = text[:10000]
            return ParsedFile(
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
                file_type="pptx",
                metric_label="Slides",
                metric_value=len(prs.slides),
                text_excerpt=excerpt,
                parser_used="python-pptx",
            )
        elif ext in ("csv",):
            # Read up to a reasonable amount for memory safety
            df = pd.read_csv(io.BytesIO(data))
            rows = len(df.index)
            # Cap rows when exporting later
            return ParsedFile(
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
                file_type="csv",
                metric_label="Rows",
                metric_value=rows,
                text_excerpt="(tabular data)",
                tables=[("Sheet1", df)],
                parser_used="pandas.read_csv",
            )
        elif ext in ("xlsx", "xlsm", "xltx", "xls"):
            # Use engine default for xlsx
            xls = pd.ExcelFile(io.BytesIO(data))
            tables: List[Tuple[str, pd.DataFrame]] = []
            total_rows = 0
            for sheet in xls.sheet_names:
                df = xls.parse(sheet)
                tables.append((sheet, df))
                total_rows += len(df.index)
            return ParsedFile(
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
                file_type="xlsx",
                metric_label="Sheets",
                metric_value=len(xls.sheet_names),
                text_excerpt="(tabular data)",
                tables=tables,
                parser_used="pandas.ExcelFile",
            )
        elif ext in ("png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"):
            return ParsedFile(
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
                file_type="image",
                metric_label="Status",
                metric_value=0,
                text_excerpt="Images are not supported for text extraction in this MVP.",
                parser_used="none",
            )
        else:
            return ParsedFile(
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
                file_type=ext or "unknown",
                metric_label="Status",
                metric_value=0,
                text_excerpt=f"Unsupported file type: .{ext}.",
                parser_used="none",
            )
    except Exception as e:  # noqa: BLE001
        return ParsedFile(
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            file_type=ext or "unknown",
            metric_label="Error",
            metric_value=0,
            text_excerpt="",
            parser_used="error",
            error=str(e),
        )
