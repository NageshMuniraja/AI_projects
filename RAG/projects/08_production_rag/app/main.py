"""Project 08 — Production RAG service (FastAPI).

Endpoints:
  GET  /health            liveness
  POST /ingest            add documents to the index   {"texts": [...], "source": "..."}
  POST /query             ask a question               {"query": "...", "k": 4}
  GET  /metrics           cache + request stats

Run:
    uvicorn app.main:app --reload --port 8000     # from projects/08_production_rag/
    # then:  curl -s localhost:8000/query -H 'content-type: application/json' \
    #              -d '{"query":"How long is the free trial?"}' | python -m json.tool

Demonstrates the production concerns from doc 11: separated ingest/query, semantic caching,
guardrails, structured logging + per-request tracing, basic rate limiting, and metrics.
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .cache import SemanticCache
from .guardrails import check_input
from .rag import RagEngine

# ---------- structured logging ----------
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger("rag")

SEED = os.path.join(os.path.dirname(__file__), "..", "data", "kb.md")
engine = RagEngine(seed_path=SEED)
cache = SemanticCache(threshold=0.96)

# ---------- naive in-memory rate limiter (per client IP) ----------
RATE_LIMIT, WINDOW = 30, 60.0  # 30 requests / 60s
_buckets: dict[str, deque] = defaultdict(deque)
_req_count = 0


def rate_limited(ip: str) -> bool:
    now = time.time()
    dq = _buckets[ip]
    while dq and now - dq[0] > WINDOW:
        dq.popleft()
    if len(dq) >= RATE_LIMIT:
        return True
    dq.append(now)
    return False


# ---------- models ----------
class IngestRequest(BaseModel):
    texts: list[str] = Field(..., description="passages/chunks to index")
    source: str = "api"


class QueryRequest(BaseModel):
    query: str
    k: int = 4


app = FastAPI(title="Helios RAG Service", version="1.0")


@app.get("/health")
def health():
    return {"status": "ok", "docs_indexed": len(engine.docs)}


@app.post("/ingest")
def ingest(req: IngestRequest):
    n = engine.ingest(req.texts, source=req.source)
    log.info(f"ingest source={req.source} added={n} total={len(engine.docs)}")
    return {"added": n, "total_docs": len(engine.docs)}


@app.post("/query")
def query(req: QueryRequest, request: Request):
    global _req_count
    _req_count += 1
    trace_id = str(uuid.uuid4())[:8]
    ip = request.client.host if request.client else "unknown"
    t0 = time.perf_counter()

    if rate_limited(ip):
        log.warning(f"[{trace_id}] rate_limited ip={ip}")
        return JSONResponse(status_code=429, content={"error": "rate limit exceeded", "trace_id": trace_id})

    # input guardrail
    gate = check_input(req.query)
    if not gate["allowed"]:
        log.warning(f"[{trace_id}] blocked reason={gate['reason']} q={req.query[:60]!r}")
        return JSONResponse(status_code=400, content={"error": gate["reason"], "trace_id": trace_id})

    # semantic cache
    from common.embeddings import embed_query
    qv = embed_query(req.query)
    cached, sim = cache.get(qv)
    if cached is not None:
        ms = round((time.perf_counter() - t0) * 1000, 1)
        log.info(f"[{trace_id}] CACHE HIT sim={sim:.3f} {ms}ms q={req.query[:60]!r}")
        return {**cached, "cached": True, "cache_similarity": round(sim, 3), "trace_id": trace_id, "latency_ms": ms}

    # retrieve + generate
    result = engine.answer(req.query, k=req.k)
    cache.put(req.query, qv, result)
    ms = round((time.perf_counter() - t0) * 1000, 1)
    log.info(f"[{trace_id}] answered refused={result['refused']} top={result['top_score']} "
             f"{ms}ms trace={result['trace']} q={req.query[:60]!r}")
    return {**result, "cached": False, "trace_id": trace_id, "latency_ms": ms}


@app.get("/metrics")
def metrics():
    return {"requests": _req_count, "docs_indexed": len(engine.docs), "cache": cache.stats()}
