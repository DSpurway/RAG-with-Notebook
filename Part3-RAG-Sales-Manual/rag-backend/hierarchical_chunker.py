import logging
from typing import Any, Dict, List, Optional

from transformers import AutoTokenizer

from docling_config import DOCLING_CHUNK_OVERLAP, DOCLING_CHUNK_SIZE
from token_utils import split_text_into_token_chunks

logger = logging.getLogger(__name__)

_TOKENIZER = None
EXCLUDED_LABELS = {"page_header", "page_footer", "caption", "reference", "footnote"}
TEXT_LABELS = {"text", "list_item", "code", "formula"}


def _get_tokenizer():
    global _TOKENIZER

    if _TOKENIZER is None:
        _TOKENIZER = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

    return _TOKENIZER


def _get_page_number(item: Any) -> Optional[int]:
    if hasattr(item, "page_number") and item.page_number is not None:
        return item.page_number

    prov = getattr(item, "prov", None)
    if prov:
        first = prov[0]
        if hasattr(first, "page_no"):
            return first.page_no
        if isinstance(first, dict):
            return first.get("page_no")

    return None


def _get_text(item: Any) -> str:
    return getattr(item, "text", "") or ""


def _get_label(item: Any) -> str:
    return getattr(item, "label", "") or ""


def extract_hierarchy(docling_doc):
    hierarchy = []
    current = {
        "chapter": None,
        "section": None,
        "subsection": None,
        "subsubsection": None,
    }

    for item, _ in docling_doc.iterate_items():
        label = _get_label(item)
        text = _get_text(item).strip()
        if not text:
            continue

        if label == "title":
            current["chapter"] = text
            current["section"] = None
            current["subsection"] = None
            current["subsubsection"] = None
        elif label == "section_header":
            if current["section"] is None:
                current["section"] = text
            elif current["subsection"] is None:
                current["subsection"] = text
            elif current["subsubsection"] is None:
                current["subsubsection"] = text
            else:
                current["subsubsection"] = text

        hierarchy.append(
            {
                "label": label,
                "text": text,
                "page_number": _get_page_number(item),
                "hierarchy": current.copy(),
            }
        )

    return hierarchy


def chunk_with_hierarchy(docling_doc, max_tokens=DOCLING_CHUNK_SIZE, overlap=DOCLING_CHUNK_OVERLAP):
    tokenizer = _get_tokenizer()
    chunks: List[Dict[str, Any]] = []
    current_hierarchy = {
        "chapter": None,
        "section": None,
        "subsection": None,
        "subsubsection": None,
    }

    for item, _ in docling_doc.iterate_items():
        label = _get_label(item)
        text = _get_text(item).strip()

        if not text or label in EXCLUDED_LABELS:
            continue

        if label == "title":
            current_hierarchy["chapter"] = text
            current_hierarchy["section"] = None
            current_hierarchy["subsection"] = None
            current_hierarchy["subsubsection"] = None
            continue

        if label == "section_header":
            if current_hierarchy["section"] is None:
                current_hierarchy["section"] = text
            elif current_hierarchy["subsection"] is None:
                current_hierarchy["subsection"] = text
            elif current_hierarchy["subsubsection"] is None:
                current_hierarchy["subsubsection"] = text
            else:
                current_hierarchy["subsubsection"] = text
            continue

        if label not in TEXT_LABELS:
            continue

        normalized_text = text
        if label == "code":
            normalized_text = f"```\n{text}\n```"
        elif label == "formula":
            normalized_text = f"${text}$"

        text_chunks = split_text_into_token_chunks(normalized_text, tokenizer, max_tokens, overlap)
        page_number = _get_page_number(item)

        for part_index, chunk_text in enumerate(text_chunks):
            chunks.append(
                {
                    "text": chunk_text,
                    "metadata": {
                        "chapter": current_hierarchy["chapter"],
                        "section": current_hierarchy["section"],
                        "subsection": current_hierarchy["subsection"],
                        "subsubsection": current_hierarchy["subsubsection"],
                        "page_number": page_number,
                        "type": label,
                        "part_index": part_index,
                        "source": "docling",
                    },
                }
            )

    logger.info("Created %s hierarchical Docling chunks", len(chunks))
    return chunks

# Made with Bob
