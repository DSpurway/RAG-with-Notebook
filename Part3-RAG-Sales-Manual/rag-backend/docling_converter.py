import logging
import shutil
import tempfile
from pathlib import Path

import pypdfium2 as pdfium
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc.document import DoclingDocument

from docling_config import (
    DOCLING_LARGE_PDF_THRESHOLD,
    DOCLING_MODELS_PATH,
    ENABLE_OCR,
    ENABLE_TABLES,
    PDF_CHUNK_SIZE,
)

logger = logging.getLogger(__name__)

_doc_converter = None


def get_pdf_page_count(pdf_path):
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        return len(pdf)
    finally:
        pdf.close()


def get_doc_converter():
    global _doc_converter

    if _doc_converter is not None:
        return _doc_converter

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_table_structure = ENABLE_TABLES
    pipeline_options.do_ocr = ENABLE_OCR

    if ENABLE_TABLES and hasattr(pipeline_options, "table_structure_options"):
        pipeline_options.table_structure_options.do_cell_matching = True

    if DOCLING_MODELS_PATH:
        if DOCLING_MODELS_PATH.exists():
            pipeline_options.artifacts_path = DOCLING_MODELS_PATH
            logger.info("Using Docling models from %s", DOCLING_MODELS_PATH)
        else:
            logger.warning("DOCLING_MODELS_PATH does not exist: %s", DOCLING_MODELS_PATH)

    _doc_converter = DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend,
            )
        },
    )

    return _doc_converter


def convert_pdf(pdf_path):
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info("Converting PDF with Docling: %s", pdf_path)
    converter = get_doc_converter()
    result = converter.convert(source=pdf_path)
    logger.info("Docling conversion completed for %s", pdf_path.name)
    return result.document


def convert_pdf_chunked(pdf_path, chunk_size=PDF_CHUNK_SIZE):
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    total_pages = get_pdf_page_count(pdf_path)
    if total_pages <= DOCLING_LARGE_PDF_THRESHOLD:
        return convert_pdf(pdf_path)

    logger.info(
        "Converting large PDF in chunks: %s (%s pages, chunk_size=%s)",
        pdf_path,
        total_pages,
        chunk_size,
    )

    converter = get_doc_converter()
    cache_dir = Path(tempfile.mkdtemp(prefix="docling_chunks_"))

    try:
        chunk_files = []

        for start_page in range(1, total_pages + 1, chunk_size):
            end_page = min(start_page + chunk_size - 1, total_pages)
            chunk_num = ((start_page - 1) // chunk_size) + 1

            logger.info(
                "Processing PDF chunk %s pages %s-%s",
                chunk_num,
                start_page,
                end_page,
            )

            result = converter.convert(source=pdf_path, page_range=(start_page, end_page))
            chunk_file = cache_dir / f"chunk_{chunk_num:04d}.json"
            result.document.save_as_json(str(chunk_file))
            chunk_files.append(chunk_file)

        docs = [DoclingDocument.load_from_json(filename=chunk_file) for chunk_file in chunk_files]
        return DoclingDocument.concatenate(docs=docs)

    except Exception:
        logger.exception("Docling chunked conversion failed for %s", pdf_path)
        raise

    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)

# Made with Bob
