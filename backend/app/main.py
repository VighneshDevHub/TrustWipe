from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import certificates, verify, wipes
from app.core.config import get_settings
from app.db.session import init_models

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Phase 1: create tables directly for fast local iteration.
    # Production should run `alembic upgrade head` instead — see
    # docs/phase1.md "Switching to Alembic migrations".
    await init_models()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [settings.PUBLIC_BASE_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wipes.router, prefix="/api/v1")
app.include_router(certificates.router, prefix="/api/v1")
app.include_router(verify.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
