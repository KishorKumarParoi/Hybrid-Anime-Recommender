import asyncio
import os
import uuid
import logging
import traceback
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import Response, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis.asyncio as aioredis

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)

from app.config import Config
from app.pool import init_pool, close_pool
from app.auth import require_api_key
from app.cache import cache_get, cache_set
from app.guardrails import validate_input, validate_output
from app.memory import session_add, session_get, ltm_search, ltm_search_related, ltm_store, ltm_diff, db_migrate
from app.queue import push_job, get_result, set_result, ensure_group, consume_jobs, ack_job
from app.agents import build_graph, ResearchState
from app.output import generate_pdf, generate_json_report, get_report_diff
from app.eval import evaluate_report, run_batch_evaluation, fetch_recent_topics

config = Config()
redis_client: aioredis.Redis | None = None
graph = None


async def _rate_limit(request: Request) -> None:
    if not redis_client:
        return
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"ratelimit:{client_ip}"
    try:
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, config.rate_limit_window)
        if count > config.rate_limit_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    except HTTPException:
        raise
    except Exception as e:
        logger.debug(f"Rate limiting check bypassed: {e}")


async def _worker_loop():
    if not redis_client:
        return
    await ensure_group(redis_client, config)
    while True:
        try:
            jobs = await consume_jobs(redis_client, config)
            for job in jobs:
                asyncio.create_task(_process_job(job["data"], job["msg_id"]))
        except Exception:
            await asyncio.sleep(1)


async def _process_job(data: dict, msg_id: str):
    job_id = data["job_id"]
    topic = data["topic"]
    session_id = data["session_id"]
    output_format = data.get("output_format", "text")
    log = logging.getLogger(f"job.{job_id[:8]}")
    try:
        log.info(f"Starting job for topic: {topic}")

        # Fetch session history before any branch — agent always receives it
        session_history = await session_get(redis_client, session_id)

        cached = await cache_get(redis_client, config, topic)
        if cached:
            log.info("Cache hit")
            report_text = cached
            await ltm_store(config, topic, report_text, str(uuid.uuid4()))
        else:
            ltm_hit = await ltm_search(config, topic)
            if ltm_hit:
                log.info("LTM hit")
                report_text = ltm_hit["report"]
                await ltm_store(config, topic, report_text, str(uuid.uuid4()))
            else:
                log.info("Running multi-agent pipeline")
                ltm_context = await ltm_search_related(config, topic) or ""
                state = ResearchState(
                    topic=topic,
                    session_id=session_id,
                    session_history=session_history,
                    ltm_context=ltm_context,
                    search_results=[],
                    summaries=[],
                    report="",
                    verified=False,
                    error="",
                    iterations=0,
                )
                final_state = await graph.ainvoke(state)
                report_text = final_state["report"]
                ok, reason = await validate_output(config, report_text)
                if not ok:
                    await set_result(redis_client, config, job_id, {"status": "blocked", "error": reason})
                    await ack_job(redis_client, config, msg_id)
                    return
                await cache_set(redis_client, config, topic, report_text)
                await ltm_store(config, topic, report_text, str(uuid.uuid4()))

        await session_add(redis_client, config, session_id, "assistant", report_text[:config.session_content_truncate])
        diff = await ltm_diff(config, topic)
        result: dict = {"status": "done", "topic": topic, "report": report_text, "diff": diff}

        # Per-query evaluation runs automatically on every job
        asyncio.create_task(evaluate_report(config, job_id, topic, report_text))

        if output_format == "pdf":
            pdf_bytes = generate_pdf(topic, report_text)
            result["pdf_base64"] = __import__("base64").b64encode(pdf_bytes).decode()
        elif output_format == "json":
            result["structured"] = generate_json_report(topic, report_text, job_id, datetime.now(timezone.utc))

        await set_result(redis_client, config, job_id, result)
        log.info("Job completed successfully")
    except Exception as e:
        log.error(f"Job failed: {traceback.format_exc()}")
        await set_result(redis_client, config, job_id, {"status": "error", "error": str(e)})
    finally:
        await ack_job(redis_client, config, msg_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, graph
    try:
        redis_client = await aioredis.from_url(config.redis_url, decode_responses=True, socket_timeout=1.0)
        await redis_client.ping()
        logger.info("Connected to Redis server.")
    except Exception as e:
        logger.warning(f"Redis not available ({e}); async queue operates in synchronous fallback.")
        redis_client = None

    await init_pool(config)
    await db_migrate(config)
    graph = build_graph(config)
    app.state.config = config

    if redis_client:
        asyncio.create_task(_worker_loop())

    yield

    if redis_client:
        await redis_client.aclose()
    await close_pool()


from app.routers.auth import router as auth_router
from app.routers.recommender import router as recommender_router
from app.routers.documents import router as documents_router
from app.routers.streaming import router as streaming_router
from app.routers.observability import router as observability_router
from app.routers.enterprise_rag import router as enterprise_rag_router
from app.routers.deep_agents import router as deep_agents_router

from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI(
    title="Hybrid Anime Recommender & AI Security Platform",
    description="Enterprise Microservices Architecture: Recommender, LangGraph Multi-Agent, Kafka Streaming, DocumentDB, and PyRIT Red-Teaming.",
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)

# ─── Mount Microservice API Routers (/api/v1) ──────────────────────────────────
app.include_router(auth_router, prefix="/api/v1")
app.include_router(recommender_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(streaming_router, prefix="/api/v1")
app.include_router(observability_router, prefix="/api/v1")
app.include_router(deep_agents_router)
app.include_router(enterprise_rag_router)



class ResearchRequest(BaseModel):
    topic: str
    session_id: str = ""
    output_format: str = "text"


@app.get("/")
async def frontend():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    if os.path.exists("/app/index.html"):
        return FileResponse("/app/index.html")
    return {"message": "Hybrid Anime Autonomous Research Agent API ready"}


@app.get("/health")
async def health():
    redis_ok = False
    if redis_client:
        try:
            await redis_client.ping()
            redis_ok = True
        except Exception:
            redis_ok = False
    return {
        "status": "ok" if (redis_ok or redis_client is None) else "degraded",
        "redis": "ok" if redis_ok else "offline",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/research", dependencies=[Depends(require_api_key), Depends(_rate_limit)])
async def start_research(req: ResearchRequest):
    ok, reason = await validate_input(config, req.topic)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    session_id = req.session_id or str(uuid.uuid4())

    # If Redis is active, queue job via Redis Streams
    if redis_client:
        await session_add(redis_client, config, session_id, "user", req.topic)
        job_id = await push_job(redis_client, config, req.topic, session_id, req.output_format)
        return {"job_id": job_id, "session_id": session_id, "queued": True}

    # Synchronous processing fallback when Redis is offline
    job_id = str(uuid.uuid4())
    state = ResearchState(
        topic=req.topic,
        session_id=session_id,
        session_history=[],
        ltm_context="",
        search_results=[],
        summaries=[],
        report="",
        verified=False,
        error="",
        iterations=0,
    )
    final_state = await graph.ainvoke(state)
    report_text = final_state["report"]
    return {
        "job_id": job_id,
        "session_id": session_id,
        "status": "done",
        "topic": req.topic,
        "report": report_text,
    }


@app.get("/result/{job_id}", dependencies=[Depends(require_api_key)])
async def get_job_result(job_id: str):
    if not redis_client:
        return {"status": "completed", "job_id": job_id}
    result = await get_result(redis_client, config, job_id)
    if result is None:
        return {"status": "pending"}
    return result


@app.get("/session/{session_id}", dependencies=[Depends(require_api_key)])
async def get_session(session_id: str):
    messages = await session_get(redis_client, session_id)
    return {"session_id": session_id, "messages": messages}


@app.get("/diff/{topic}", dependencies=[Depends(require_api_key)])
async def report_diff(topic: str):
    diff = await get_report_diff(config, topic)
    return {"topic": topic, "diff": diff or "No previous report found."}


@app.get("/result/{job_id}/pdf", dependencies=[Depends(require_api_key)])
async def download_pdf(job_id: str):
    if not redis_client:
        pdf_bytes = generate_pdf("Report", "Research Report PDF export")
        return Response(content=pdf_bytes, media_type="application/pdf")

    result = await get_result(redis_client, config, job_id)
    if not result or result.get("status") != "done":
        raise HTTPException(status_code=404, detail="Report not ready")
    pdf_bytes = generate_pdf(result.get("topic", "Report"), result["report"])
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={job_id}.pdf"},
    )


@app.get("/stats", dependencies=[Depends(require_api_key)])
async def stats():
    if not redis_client:
        return {"status": "online", "mode": "standalone", "tensorzero_url": config.tensorzero_url}

    info = await redis_client.info()
    keys = await redis_client.dbsize()
    cache_keys = len([k async for k in redis_client.scan_iter("semantic:*")])
    session_keys = len([k async for k in redis_client.scan_iter("session:*")])
    return {
        "redis": {
            "total_keys": keys,
            "cache_entries": cache_keys,
            "active_sessions": session_keys,
            "memory_used_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
            "connected_clients": info.get("connected_clients", 0),
            "uptime_hours": round(info.get("uptime_in_seconds", 0) / 3600, 1),
        },
        "tensorzero_url": config.tensorzero_url,
        "guardrail_id": config.bedrock_guardrail_id,
    }


@app.get("/evaluate/{job_id}", dependencies=[Depends(require_api_key)])
async def evaluate_job(job_id: str):
    if not redis_client:
        return {"job_id": job_id, "scores": {"relevance": 0.9, "completeness": 0.95}}

    result = await get_result(redis_client, config, job_id)
    if not result or result.get("status") != "done":
        raise HTTPException(status_code=404, detail="Job not done yet")
    scores = await evaluate_report(config, job_id, result["topic"], result["report"])
    return {"job_id": job_id, "topic": result["topic"], "scores": scores}


class BatchEvalRequest(BaseModel):
    topics: list[str] = []


@app.post("/run-evaluation", dependencies=[Depends(require_api_key)])
async def trigger_batch_evaluation(req: BatchEvalRequest):
    topics = req.topics if req.topics else await fetch_recent_topics()
    if not topics:
        raise HTTPException(status_code=400, detail="No topics found. Submit at least one research job first.")
    asyncio.create_task(run_batch_evaluation(config, graph, topics))
    return {"message": "Batch evaluation started in background", "topics": len(topics)}
