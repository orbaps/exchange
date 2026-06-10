import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dashboard.api.auth import router as auth_router
from dashboard.api.public import router as public_router
from dashboard.api.admin import router as admin_router
from dashboard.api.websockets import router as ws_router
from dashboard.api.replay import router as replay_router
from dashboard.api.evaluation import router as evaluation_router
from dashboard.api.federation import router as federation_router
from dashboard.dependencies import event_bridge, aggregator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IICPC Operator Dashboard API",
    description="Control panel and streaming live analytics for the IICPC Competition Runtime",
    version="1.0.0"
)

# Enable CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(auth_router)
app.include_router(public_router)
app.include_router(admin_router)
app.include_router(ws_router)
app.include_router(replay_router)
app.include_router(evaluation_router)
app.include_router(federation_router)

@app.on_event("startup")
async def startup_event():
    # Bind the current running event loop to the event bridge
    loop = asyncio.get_running_loop()
    event_bridge.set_loop(loop)
    logger.info("EventBridge bound to the active FastAPI event loop.")
    
    # Attempt automatic state rebuild from default journals if they exist
    t_journal = "dashboard_run_artifacts/t1_journal.jsonl"
    h_journal = "dashboard_run_artifacts/hosting_journal.jsonl"
    
    t_ok = aggregator.rebuild_from_tournament_journal(t_journal)
    h_ok = aggregator.rebuild_from_hosting_journal(h_journal)
    
    if t_ok or h_ok:
        logger.info(f"Automatically rebuilt initial dashboard state (tournament: {t_ok}, hosting: {h_ok}).")
    else:
        logger.info("No default journal files found. Initializing with empty state.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Dashboard API shutting down.")
