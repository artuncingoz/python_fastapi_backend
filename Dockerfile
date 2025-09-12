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

COPY . .

# make scripts executable & strip CRLF if they slipped in from Windows
RUN chmod +x /app/start.sh /app/start_worker.sh && \
    sed -i 's/\r$//' /app/start.sh /app/start_worker.sh || true

EXPOSE 8000
CMD ["sh", "/app/start.sh"]

