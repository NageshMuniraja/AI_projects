# Production RAG service — container image
# Build context should be the REPO ROOT so we can copy common/ too:
#   docker build -f projects/08_production_rag/Dockerfile -t helios-rag .
#   docker run -p 8000:8000 --env-file .env helios-rag

FROM python:3.12-slim

WORKDIR /srv

# System deps kept minimal; add build-essential only if a wheel needs compiling.
ENV PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1

# Install just what the service needs (lighter than the full course requirements).
RUN pip install --no-cache-dir \
    "openai>=1.30" "anthropic>=0.34" python-dotenv \
    chromadb rank-bm25 numpy \
    "fastapi>=0.110" "uvicorn[standard]>=0.29" "pydantic>=2.6"

# Copy shared helpers and the service.
COPY common /srv/common
COPY projects/08_production_rag /srv/projects/08_production_rag

WORKDIR /srv/projects/08_production_rag
EXPOSE 8000

# 2 workers as a starting point; tune to your CPU/latency target.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
