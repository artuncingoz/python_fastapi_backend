# app/services/summarize.py
import os
from app.services.summarize_llm import summarize_text_llm

BACKEND = os.getenv("SUMMARIZER_BACKEND", "llm").lower()  # "llm" or "rule"

def summarize_text_rule(text: str) -> str:
    t = (text or "").strip()
    if len(t) <= 280:
        return t
    return t[:277] + "..."

def summarize_text(text: str) -> str:
    if BACKEND == "rule":
        return summarize_text_rule(text)
    return summarize_text_llm(text)
