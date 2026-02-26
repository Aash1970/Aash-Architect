"""
Career Architect Pro — FastAPI backend entry point.

Run with:
    uvicorn backend.main:app --reload

Environment variables required for JWT authentication:
    SUPABASE_JWT_SECRET      — HS256 JWT secret (from Supabase Project Settings → API)

Optional:
    SUPABASE_JWT_ALGORITHM   — "HS256" (default) or "RS256"
    SUPABASE_JWT_PUBLIC_KEY  — PEM public key (RS256 only)
    CORS_ALLOWED_ORIGINS     — comma-separated list, default "http://localhost:3000"
    LOG_LEVEL                — DEBUG | INFO | WARNING | ERROR (default INFO)
    LOG_FORMAT               — "json" | "text" (default "text")
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.admin.admin_service import AdminService
from app.lifecycle.retention import RetentionService
from app.lifecycle.versioning import VersioningService
from app.logging.logger import get_logger
from app.security.package_builder import PackageBuilder
from app.services.ats_service import ATSService
from app.services.auth_service import AuthService
from app.services.cv_service import CVService
from app.services.data_service import DataService
from app.services.role_service import RoleService
from app.services.tier_service import TierService

from backend.api.middleware.logging import StructuredLoggingMiddleware
from backend.api.routers import admin, ats, auth, cv, tier

_VERSION = "3.0.0"
_logger = get_logger("backend.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Build the service dependency graph once at startup and attach to app.state.
    Teardown logging happens on exit.
    """
    ds = DataService()
    rs = RoleService()
    ts = TierService(ds)
    vs = VersioningService()
    pb = PackageBuilder()
    ret = RetentionService()

    cv_svc = CVService(ds, rs, ts, vs, pb)
    auth_svc = AuthService(ds)
    admin_svc = AdminService(ds, rs, ret)
    ats_svc = ATSService(cv_svc, ts)

    app.state.data_service = ds
    app.state.auth_service = auth_svc
    app.state.cv_service = cv_svc
    app.state.role_service = rs
    app.state.tier_service = ts
    app.state.ats_service = ats_svc
    app.state.admin_service = admin_svc

    _logger.info("Career Architect Pro backend v%s started", _VERSION)
    yield
    _logger.info("Backend shutting down")


def create_app() -> FastAPI:
    """Factory function — creates and configures the FastAPI application."""

    app = FastAPI(
        title="Career Architect Pro API",
        description=(
            "Production-ready REST API for Career Architect Pro. "
            "All endpoints delegate to the existing service layer — "
            "no business logic is duplicated here."
        ),
        version=_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    allowed_origins = [
        o.strip()
        for o in os.environ.get(
            "CORS_ALLOWED_ORIGINS", "http://localhost:3000"
        ).split(",")
        if o.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # ── Structured request logging ─────────────────────────────────────────────
    app.add_middleware(StructuredLoggingMiddleware)

    # ── Domain routers ────────────────────────────────────────────────────────
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(cv.router,   prefix="/cv",   tags=["cv"])
    app.include_router(ats.router,  prefix="/ats",  tags=["ats"])
    app.include_router(tier.router, prefix="/tier", tags=["tier"])
    app.include_router(admin.router, prefix="/admin", tags=["admin"])

    # ── System endpoints ──────────────────────────────────────────────────────
    @app.get("/health", tags=["system"], summary="Liveness check")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/version", tags=["system"], summary="API version")
    async def version() -> dict:
        return {
            "version": _VERSION,
            "service": "Career Architect Pro",
            "environment": os.environ.get("ENVIRONMENT", "development"),
        }

    # ── Global exception handlers ─────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        _logger.error(
            "Unhandled exception on %s %s: %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": {"code": "internal_error", "message": "An unexpected error occurred."}},
        )

    return app


app = create_app()
