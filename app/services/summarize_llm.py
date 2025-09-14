# app/services/summarize_llm.py
import os
from functools import lru_cache
from transformers import pipeline

SUM_MAX_INPUT_TOKENS = int(os.getenv("SUM_MAX_INPUT_TOKENS", "512"))
SUM_MAX_OUTPUT_TOKENS = int(os.getenv("SUM_MAX_OUTPUT_TOKENS", "128"))
SUM_MIN_OUTPUT_TOKENS = int(os.getenv("SUM_MIN_OUTPUT_TOKENS", "20"))

HF_OFFLINE = os.getenv("HF_HUB_OFFLINE", "1") == "1"
MODEL_LOCAL_DIR = os.getenv("MODEL_LOCAL_DIR", "").strip()
SUMMARIZER_MODEL = os.getenv("SUMMARIZER_MODEL", "t5-small").strip()

def _check_local_dir(path: str) -> bool:
    if not path:
        return False
    try:
        return os.path.isdir(path) and os.path.exists(os.path.join(path, "config.json"))
    except Exception:
        return False

@lru_cache(maxsize=1)
def _get_pipeline():
    """
    Prefer a local baked directory (MODEL_LOCAL_DIR). If not present and we're online,
    fall back to the Hub id (SUMMARIZER_MODEL). In offline mode without local files, error.
    """
    kwargs = dict(
        task="summarization",
        framework="pt",
        device=-1,                      # CPU
        clean_up_tokenization_spaces=True,
    )

    local_ok = _check_local_dir(MODEL_LOCAL_DIR)
    if local_ok:
        return pipeline(model=MODEL_LOCAL_DIR, tokenizer=MODEL_LOCAL_DIR, **kwargs)

    # If we’re here, local dir isn't usable. If offline, we can’t fetch from hub.
    if HF_OFFLINE:
        raise RuntimeError(
            f"MODEL_LOCAL_DIR '{MODEL_LOCAL_DIR}' not found/complete and HF_HUB_OFFLINE=1. "
            f"Rebuild the image with the model baked in."
        )

    # Online fallback (not recommended for Koyeb)
    return pipeline(model=SUMMARIZER_MODEL, tokenizer=SUMMARIZER_MODEL, **kwargs)

def summarize_text_llm(text: str) -> str:
    pipe = _get_pipeline()
    # T5 benefits from "summarize:" prefix; harmless for others.
    prefix = "summarize: " if "t5" in (MODEL_LOCAL_DIR + SUMMARIZER_MODEL).lower() else ""
    t = (text or "").strip()
    if not t:
        return ""

    outs = pipe(
        prefix + t,
        truncation=True,
        max_length=SUM_MAX_OUTPUT_TOKENS,
        min_length=SUM_MIN_OUTPUT_TOKENS,
    )
    return (outs[0]["summary_text"] or "").strip()
