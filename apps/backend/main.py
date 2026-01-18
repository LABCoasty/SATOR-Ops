"""
SATOR Ops - Decision Infrastructure for Physical Systems

FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Configuration
from config import config

# API Routers (Main Branch)
from app.api import agent_tools, audit, simulation
from app.api import replay as replay_v2  # New Replay Engine

# API Routers (Temporal Branch - preserving frontend compatibility)
from app.api.routes import decisions, evidence, artifacts, telemetry, temporal
from app.api.routes import replay as replay_v1  # Legacy/Frontend Replay Engine
from app.api.websocket import router as websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup: ensure data directories exist
    config.get_data_path("telemetry")
    config.get_data_path("events")
    config.get_data_path("audit")

    print("SATOR Ops starting with config:")
    print(f"  - Data directory: {config.data_dir}")
    print(f"  - Simulation seed: {config.simulation_seed}")
    print(f"  - LeanMCP enabled: {config.enable_leanmcp}")
    print(f"  - Kairo enabled: {config.enable_kairo}")
    print(f"  - Arize enabled: {config.enable_arize}")
    print(f"  - Browserbase enabled: {config.enable_browserbase}")

    yield

    # Shutdown: cleanup if needed
    print("SATOR Ops shutting down")


app = FastAPI(
    title="SATOR Ops",
    description="Decision Infrastructure for Physical Systems - A Decision Compiler that structures messy, unreliable reality into formal decision states and immutable records.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
# ---------------------------------------------------------
# Legacy/Frontend Compatible Routes (from Temporal Branch)
app.include_router(decisions.router, prefix="/api/decisions", tags=["decisions"])
app.include_router(evidence.router, prefix="/api/evidence", tags=["evidence"])
app.include_router(artifacts.router, prefix="/api/artifacts", tags=["artifacts"])
app.include_router(telemetry.router, prefix="/api/telemetry", tags=["telemetry"])
app.include_router(replay_v1.router, prefix="/api/replay", tags=["replay (v1)"])  # Used by Frontend
app.include_router(temporal.router, prefix="/api/temporal", tags=["temporal"])
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])

# New Core Routes (from Main Branch)
app.include_router(simulation.router, prefix="/simulation", tags=["Simulation"])
app.include_router(replay_v2.router, prefix="/replay", tags=["Replay (v2)"])      # New Implementation
app.include_router(audit.router, prefix="/audit", tags=["Audit"])
app.include_router(agent_tools.router, prefix="/agent", tags=["Agent Tools"])


@app.get("/")
async def root():
    """Serve the HTML interface"""
    from fastapi.responses import FileResponse
    static_dir = Path(__file__).parent / "app" / "static"
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "name": "SATOR Ops",
        "version": "0.1.0",
        "status": "operational",
        "integrations": {
            "leanmcp": config.enable_leanmcp,
            "kairo": config.enable_kairo,
            "arize": config.enable_arize,
            "browserbase": config.enable_browserbase,
        }
    }


@app.get("/health")
async def health():
    """Simple health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
