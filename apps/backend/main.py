from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import decisions, evidence, telemetry
from app.api.routes import artifacts as artifacts_original
from app.api.routes import scenarios, incidents, vision
from app.api.websocket import router as websocket_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield


app = FastAPI(
    title="SATOR API",
    description="Decision Infrastructure for Physical Systems",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.api_env == "development" else settings.allowed_origins,
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


@app.get("/")
async def root():
    return {"name": "SATOR API", "version": "0.1.0", "status": "operational"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
