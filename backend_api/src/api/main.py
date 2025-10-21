from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from src.config import settings
from src.services.parse import parse_file
from src.services.excel import build_workbook

# FastAPI app with basic metadata
app = FastAPI(
    title="Document Parsing & Export API (MVP)",
    description="Accepts uploaded files and returns a generated Excel summary. No DB, no AI.",
    version="0.1.0",
)

# CORS: restrict to frontend 3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# PUBLIC_INTERFACE
@app.get("/health", summary="Health Check", tags=["system"])
def health_check():
    """Health endpoint to verify service is up."""
    return {"status": "ok"}


# PUBLIC_INTERFACE
@app.post(
    "/export",
    summary="Upload files and receive Excel export",
    tags=["export"],
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
            },
            "description": "Generated Excel workbook",
        },
        400: {"description": "Validation error"},
    },
)
async def export(files: List[UploadFile] = File(..., description="One or more files to parse")):
    """Accept multiple files, parse best-effort, and return an Excel workbook.

    - Supports pdf, docx, pptx, csv, xlsx.
    - Non-fatal: errors captured per file and included in Metadata/ Summary.
    - Streams the resulting xlsx back to the client.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    parsed_results = []
    for f in files:
        content = await f.read()
        if len(content) > settings.max_file_size_bytes():
            parsed_results.append(
                parse_file(f.filename, f.content_type or "", b"")  # will mark as unsupported
            )
            parsed_results[-1].error = f"File too large. Limit is {settings.MAX_FILE_SIZE_MB} MB."
            continue
        result = parse_file(f.filename, f.content_type or "", content)
        parsed_results.append(result)

    wb_bytes = build_workbook(parsed_results)
    headers = {
        "Content-Disposition": 'attachment; filename="parsed_export.xlsx"'
    }
    return StreamingResponse(
        wb_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
