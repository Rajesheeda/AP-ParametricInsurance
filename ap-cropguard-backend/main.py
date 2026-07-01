"""
AP-CropGuard — FastAPI Application Entry Point
================================================
Wires all routers and middleware together.
"""

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

load_dotenv()

from routers import district, parametric, photo, meta
from routers.parametric import get_backtest_results, get_premium_table

# ---------------------------------------------------------------------------
# LIFESPAN
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 50)
    print("AP-CropGuard Backend Starting...")
    print("District: Kurnool, Andhra Pradesh")
    print("Crops: Cotton, Groundnut, Redgram, Jowar, Sunflower")
    print("Engines: SPI, VCI, Actuarial, Backtest, Bayesian, Photo, Fraud")
    print("API Docs: http://127.0.0.1:8000/docs")
    print("Status: OPERATIONAL")
    print("=" * 50)
    yield
    print("AP-CropGuard Backend shutting down.")

# ---------------------------------------------------------------------------
# APP
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AP-CropGuard API",
    description=(
        "Parametric Crop Insurance and Rapid Disaster Loss Assessment System — "
        "Kurnool District, Andhra Pradesh"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    # Demo-day safety: allow any localhost/127.0.0.1 port so a port conflict
    # (e.g. backend bumped to 8010) never silently breaks the UI with CORS.
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------------------------

app.include_router(meta.router,        prefix="/api/v1")
app.include_router(district.router,    prefix="/api/v1")
app.include_router(parametric.router,  prefix="/api/v1")
app.include_router(photo.router,       prefix="/api/v1")

# Backtest and insurance endpoints also accessible without /parametric prefix
app.add_api_route(
    "/api/v1/backtest/results",
    get_backtest_results,
    methods=["GET"],
    tags=["backtest"],
    summary="Backtest results (short path)",
)
app.add_api_route(
    "/api/v1/insurance/premium-table",
    get_premium_table,
    methods=["GET"],
    tags=["insurance"],
    summary="Premium table (short path)",
)

# ---------------------------------------------------------------------------
# ROOT
# ---------------------------------------------------------------------------

@app.get("/", tags=["root"])
def root():
    return {
        "system":      "AP-CropGuard",
        "version":     "1.0.0",
        "status":      "operational",
        "district":    "Kurnool, Andhra Pradesh",
        "description": (
            "Parametric Crop Insurance and Rapid Disaster Loss Assessment System"
        ),
        "docs":        "/docs",
        "health":      "/api/v1/meta/health",
        "timestamp":   datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
