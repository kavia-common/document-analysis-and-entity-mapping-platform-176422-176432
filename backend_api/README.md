# Backend API (FastAPI) — Document Analyzer MVP

## Overview
This FastAPI service accepts uploaded documents and returns a generated Excel (.xlsx) report that summarizes extracted content. It supports multiple file types, performs best-effort parsing, and streams the resulting Excel file back to the client. There is no database in this MVP.

- Framework: FastAPI
- Default Port: 3001
- CORS: Allows http://localhost:3000 by default

## Quick Start
Prerequisites:
- Python 3.10+
- pip

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the API:
```bash
# From this backend_api directory
uvicorn src.api.main:app --host 0.0.0.0 --port 3001
```

Access:
- Health: http://localhost:3001/health
- OpenAPI schema: http://localhost:3001/openapi.json
- Swagger UI: http://localhost:3001/docs

## Running via Preview System
If using the Kavia preview environment:
- Ensure the backend is started on port 3001:
  ```bash
  uvicorn src.api.main:app --host 0.0.0.0 --port 3001
  ```
- The frontend expects the backend at http://localhost:3001 by default. If the preview system assigns a different URL, update the frontend `src/api/client.js` accordingly.

## Environment Variables (if any)
The backend reads configuration from environment variables with sensible defaults. See `src/config.py`.

- STORAGE_DIR (default: "./storage")
- MAX_FILE_SIZE_MB (default: 25)
- ALLOWED_ORIGINS (default: "http://localhost:3000")
  - Comma-separated list; used for CORS. Ensure it includes the exact frontend origin.

You can copy `.env.example` to `.env` and export variables in your shell or use a process manager that injects them.

Example:
```bash
# Local development
export STORAGE_DIR=./storage
export MAX_FILE_SIZE_MB=25
export ALLOWED_ORIGINS=http://localhost:3000

# Preview environment (replace with your actual preview frontend origin)
export ALLOWED_ORIGINS=https://vscode-internal-39135-beta.beta01.cloud.kavia.ai:3000
```

## API
Base URL: http://localhost:3001

- GET /health
  - Summary: Health Check
  - Response: {"status": "ok"}

- POST /export
  - Summary: Upload files and receive Excel export
  - Content-Type: multipart/form-data
  - Field: files[] (one or more files)
  - Response:
    - 200 application/vnd.openxmlformats-officedocument.spreadsheetml.sheet (Excel workbook)
    - 400 Validation error (e.g., when no files provided)

OpenAPI spec is generated based on the FastAPI app and available at /openapi.json. A snapshot is also stored in `interfaces/openapi.json`.

## Supported File Types
- pdf
- docx
- pptx
- xlsx
- csv

Notes:
- Images are not supported for text extraction in this MVP; they are marked unsupported.
- Excel is generated on the fly and streamed back.

## How to Use (Upload and Export Flow)
1. Client submits a multipart/form-data request to POST /export with files[].
2. Backend parses each file best-effort by type, collecting:
   - Metrics (pages/paragraphs/slides/rows/sheets)
   - Text excerpts (where applicable, capped)
   - Tabular data (for CSV/XLSX, limited rows per table when exporting)
   - Metadata and errors (if any)
3. Backend generates a multi-sheet Excel workbook:
   - Summary, Extracts, Tables, and Metadata
4. Backend streams the Excel file as the response with an attachment Content-Disposition.

## Troubleshooting
- PDF parsing fails:
  - Ensure PDFs are text-based (not scanned). This MVP does not perform OCR.
- Large files:
  - Files above MAX_FILE_SIZE_MB (default 25MB) will be marked as too large or unsupported.
- CORS errors:
  - Ensure the frontend runs on http://localhost:3000 and ALLOWED_ORIGINS includes that origin.
- Dependency issues:
  - Re-run `pip install -r requirements.txt`.
- 422/400 errors:
  - Confirm the request uses multipart/form-data and includes at least one file under the `files` field.

## Notes and Next Steps
- No database is used in this MVP.
- AI entity extraction is not integrated in this version; focus is on parsing and Excel export.
- Consider environment-based configuration for the frontend base URL and ALLOWED_ORIGINS for different deployments.
