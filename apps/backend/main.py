from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from app.api import agent_tools, audit, ingest, overshoot_test, replay, simulation
from app.api.routes import decisions, evidence, telemetry, scenarios, incidents, vision
from app.api.routes import artifacts as artifacts_original
from app.api.websocket import router as websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan - initialize vision processing queue with LeanMCP."""
    import asyncio
    from app.services.vision_processor import get_vision_queue
    
    # Start vision processing queue on startup
    vision_queue = get_vision_queue()
    vision_queue.start()
    
    # Create background task for queue processing
    loop = asyncio.get_running_loop()
    background_task = loop.create_task(vision_queue._background_processor())
    
    print(f"✅ Vision processing queue started (delay: {config.vision_processing_delay_ms}ms)")
    print("✅ LeanMCP background processor running")
    
    yield
    
    # Stop vision queue on shutdown
    vision_queue.stop()
    background_task.cancel()
    try:
        await background_task
    except asyncio.CancelledError:
        pass
    print("Vision processing queue stopped")


app = FastAPI(
    title="SATOR API",
    description="Decision Infrastructure for Physical Systems",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Original routes
app.include_router(decisions.router, prefix="/api/decisions", tags=["decisions"])
app.include_router(evidence.router, prefix="/api/evidence", tags=["evidence"])
app.include_router(artifacts_original.router, prefix="/api/artifacts", tags=["artifacts"])
app.include_router(telemetry.router, prefix="/api/telemetry", tags=["telemetry"])

# New SATOR routes
app.include_router(scenarios.router, prefix="/api", tags=["scenarios"])
app.include_router(incidents.router, prefix="/api", tags=["incidents"])
app.include_router(vision.router, prefix="/api", tags=["vision"])

# WebSocket
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])
app.include_router(simulation.router, prefix="/simulation", tags=["Simulation"])
app.include_router(replay.router, prefix="/replay", tags=["Replay"])
app.include_router(audit.router, prefix="/audit", tags=["Audit"])
app.include_router(ingest.router, prefix="/ingest", tags=["Ingest"])
app.include_router(agent_tools.router, prefix="/agent", tags=["Agent Tools"])
try:
    app.include_router(overshoot_test.router, prefix="/overshoot-test", tags=["Overshoot Testing"])
    print("✅ Overshoot test router loaded")
except Exception as e:
    print(f"⚠️  Failed to load overshoot_test router: {e}")
    import traceback
    traceback.print_exc()


@app.get("/")
async def root():
    return {"name": "SATOR API", "version": "0.1.0", "status": "operational"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)