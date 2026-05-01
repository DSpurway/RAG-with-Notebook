import logging
from typing import Callable, List

from sentence_splitter import SentenceSplitter

logger = logging.getLogger(__name__)


def _count_tokens(tokenizer: Callable, text: str) -> int:
    if hasattr(tokenizer, "encode"):
        return len(tokenizer.encode(text, add_special_tokens=False))

    tokens = tokenizer(text)
    if isinstance(tokens, dict):
        input_ids = tokens.get("input_ids", [])
        if input_ids and isinstance(input_ids[0], list):
            return len(input_ids[0])
        return len(input_ids)

    return len(tokens)


def split_text_into_token_chunks(text, tokenizer, max_tokens, overlap):
    if not text or not text.strip():
        return []

    splitter = SentenceSplitter(language="en")
    sentences = [sentence.strip() for sentence in splitter.split(text) if sentence.strip()]
    if not sentences:
        sentences = [text.strip()]

    chunks: List[str] = []
    current_sentences: List[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = _count_tokens(tokenizer, sentence)

        if sentence_tokens > max_tokens:
            if current_sentences:
                chunks.append(" ".join(current_sentences).strip())
                current_sentences = []
                current_tokens = 0
            chunks.append(sentence)
            continue

        if current_sentences and current_tokens + sentence_tokens > max_tokens:
            chunks.append(" ".join(current_sentences).strip())

            if overlap > 0:
                overlap_sentences: List[str] = []
                overlap_tokens = 0
                for previous_sentence in reversed(current_sentences):
                    previous_tokens = _count_tokens(tokenizer, previous_sentence)
                    if overlap_sentences and overlap_tokens + previous_tokens > overlap:
                        break
                    overlap_sentences.insert(0, previous_sentence)
                    overlap_tokens += previous_tokens
                current_sentences = overlap_sentences
                current_tokens = overlap_tokens
            else:
                current_sentences = []
                current_tokens = 0

        current_sentences.append(sentence)
        current_tokens += sentence_tokens

    if current_sentences:
        chunks.append(" ".join(current_sentences).strip())

    logger.debug("Split text into %s token-aware chunks", len(chunks))
    return chunks

# Made with Bob
