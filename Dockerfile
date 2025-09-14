# Dockerfile
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


ARG SUMMARIZER_MODEL=sshleifer/distilbart-cnn-12-6
ENV SUMMARIZER_MODEL=${SUMMARIZER_MODEL}

# --- Bake the model into /models/<safe-name> ---
RUN python - <<'PY'
import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
mid = os.environ["SUMMARIZER_MODEL"]
safe = mid.replace("/", "-")
local_dir = f"/models/{safe}"
os.makedirs(local_dir, exist_ok=True)
tok = AutoTokenizer.from_pretrained(mid, cache_dir="/models", use_fast=True)
mdl = AutoModelForSeq2SeqLM.from_pretrained(mid, cache_dir="/models")
tok.save_pretrained(local_dir)
mdl.save_pretrained(local_dir)
print("Baked model:", mid, "->", local_dir)
PY

# --- Runtime env: force offline & tell app where the baked model lives ---
ENV HF_HUB_OFFLINE=1
ENV MODEL_LOCAL_DIR=/models/${SUMMARIZER_MODEL//\//-}
ENV SUMMARIZER_BACKEND=llm
ENV SUM_MAX_INPUT_TOKENS=512
ENV SUM_MAX_OUTPUT_TOKENS=128
ENV SUM_MIN_OUTPUT_TOKENS=20

COPY . .

RUN chmod +x /app/start.sh /app/start_worker.sh && \
    sed -i 's/\r$//' /app/start.sh /app/start_worker.sh || true

EXPOSE 8000
CMD ["sh", "/app/start.sh"]
