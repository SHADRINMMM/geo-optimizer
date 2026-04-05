from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import engine, Base

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if not exist (handled by alembic in prod)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="GEO Optimizer API",
    description="AI Search Visibility Optimization",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else [
        "https://ai.causabi.com",
        "https://causabi.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.api.v1 import analyze, sites, monitor, profile
app.include_router(analyze.router, prefix="/api/v1", tags=["analyze"])
app.include_router(sites.router, prefix="/api/v1", tags=["sites"])
app.include_router(monitor.router, prefix="/api/v1", tags=["monitor"])
app.include_router(profile.router, tags=["profile"])  # /b/<slug> — public hosted pages


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.APP_ENV}
