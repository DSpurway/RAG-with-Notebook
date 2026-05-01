import os
from pathlib import Path

USE_DOCLING = os.getenv("USE_DOCLING", "false").lower() == "true"
ENABLE_TABLES = os.getenv("ENABLE_TABLES", "true").lower() == "true"
ENABLE_OCR = os.getenv("ENABLE_OCR", "false").lower() == "true"

DOCLING_CHUNK_SIZE = int(os.getenv("DOCLING_CHUNK_SIZE", "768"))
DOCLING_CHUNK_OVERLAP = int(os.getenv("DOCLING_CHUNK_OVERLAP", "50"))

PDF_CHUNK_SIZE = int(os.getenv("PDF_CHUNK_SIZE", "100"))
DOCLING_LARGE_PDF_THRESHOLD = int(os.getenv("DOCLING_LARGE_PDF_THRESHOLD", "100"))

DOCLING_MODELS_PATH_RAW = os.getenv("DOCLING_MODELS_PATH", "/app/docling-models")
DOCLING_MODELS_PATH = Path(DOCLING_MODELS_PATH_RAW) if DOCLING_MODELS_PATH_RAW else None


def docling_config_dict():
    return {
        "use_docling": USE_DOCLING,
        "enable_tables": ENABLE_TABLES,
        "enable_ocr": ENABLE_OCR,
        "chunk_size": DOCLING_CHUNK_SIZE,
        "chunk_overlap": DOCLING_CHUNK_OVERLAP,
        "pdf_chunk_size": PDF_CHUNK_SIZE,
        "large_pdf_threshold": DOCLING_LARGE_PDF_THRESHOLD,
        "models_path": str(DOCLING_MODELS_PATH) if DOCLING_MODELS_PATH else None,
    }

# Made with Bob
