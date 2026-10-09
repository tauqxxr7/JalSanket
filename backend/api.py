"""Read-only same-origin API and static UI. No AWS credentials or user uploads."""
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .evidence import build_evidence
from .models import Contract, EvidencePackage, Provenance, Observation, Station, Quality
from .provider import CSVProvider, ROOT, SourceUnavailable, START, END

logger = logging.getLogger("jalsanket")
logging.basicConfig(level=logging.INFO)


class StationSummary(Contract):
    station_group_key: str
    label: str
    district: str
    assessment: str
    quality: str
    completeness: float
    flags: int
    evaluated: int
    next_action: str


class NetworkResponse(Contract):
    provenance: Provenance
    window_start: str
    window_end_exclusive: str
    clock_basis: str
    stations: list[StationSummary]


class StationResponse(Contract):
    station: Station
    observations: list[Observation]
    plot_observations: list[Observation]
    quality: Quality
    provenance: Provenance
    flagged_ids: list[str]


def create_app(provider=None):
    provider = provider or CSVProvider()

    @asynccontextmanager
    async def lifespan(app):
        app.state.packages = {}
        app.state.source_error = None
        try:
            provenance, stations, records = provider.load()
            app.state.provenance = provenance
            app.state.records = records
            for key, station in stations.items():
                app.state.packages[key] = build_evidence(station, records[key], provenance)
        except SourceUnavailable as error:
            app.state.source_error = str(error)
            logger.warning(json.dumps({"processing_stage": "snapshot_load", "status": "UNAVAILABLE", "error": "Snapshot unavailable or invalid"}))
        yield

    app = FastAPI(title="JalSanket", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def request_log(request: Request, call_next):
        request_id, start = str(uuid4()), perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # Unexpected failure is visible and sanitized; never a normal result.
            logger.error(json.dumps({"request_id": request_id, "processing_stage": "api", "status": "ERROR", "error": "Unhandled internal error"}))
            response = JSONResponse({"detail": "Internal error", "request_id": request_id}, status_code=500)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        logger.info(json.dumps({"request_id": request_id, "processing_stage": "http", "status": response.status_code, "latency_ms": round((perf_counter() - start) * 1000, 2), "timestamp": datetime.now(timezone.utc).isoformat()}))
        return response

    def ensure_source():
        if app.state.source_error:
            raise HTTPException(503, "Official snapshot unavailable or invalid. Run the documented acquisition step.")

    @app.get("/api/health")
    def health():
        ensure_source()
        return {"status": "ready", "mode": app.state.provenance.data_mode, "aws_deployed": False}

    @app.get("/api/network", response_model=NetworkResponse)
    def network(request: Request):
        ensure_source()
        if request.query_params:
            raise HTTPException(422, "This bounded endpoint accepts no query parameters.")
        packages = sorted(app.state.packages.values(), key=lambda p: (-p.flagged_observations, p.station.label))
        return NetworkResponse(provenance=app.state.provenance, window_start=START.isoformat(), window_end_exclusive=END.isoformat(), clock_basis="SOURCE_CLOCK_TIMEZONE_UNVERIFIED", stations=[StationSummary(station_group_key=p.station.station_group_key, label=p.station.label, district=p.station.district, assessment=p.assessment, quality=p.quality.state, completeness=p.quality.completeness, flags=p.flagged_observations, evaluated=p.evaluated_observations, next_action=p.next_check.action) for p in packages])

    @app.get("/api/stations/{station_group_key}/evidence", response_model=EvidencePackage)
    def evidence(station_group_key: str, request: Request):
        ensure_source()
        if request.query_params:
            raise HTTPException(422, "This bounded endpoint accepts no query parameters.")
        if station_group_key not in app.state.packages:
            raise HTTPException(404, "Unknown internal station grouping.")
        return app.state.packages[station_group_key]

    @app.get("/api/stations/{station_group_key}", response_model=StationResponse)
    def station_history(station_group_key: str, request: Request):
        ensure_source()
        if request.query_params:
            raise HTTPException(422, "This bounded endpoint accepts no query parameters.")
        if station_group_key not in app.state.packages:
            raise HTTPException(404, "Unknown internal station grouping.")
        package = app.state.packages[station_group_key]
        from .quality import assess
        from .spike import detect
        _, clean = assess(app.state.records[station_group_key])
        return StationResponse(station=package.station, observations=app.state.records[station_group_key], plot_observations=clean, quality=package.quality, provenance=package.provenance, flagged_ids=[row.observation_id for i,row in enumerate(clean) if detect(clean,i).outcome == "FLAG"])

    app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
    return app


app = create_app()
