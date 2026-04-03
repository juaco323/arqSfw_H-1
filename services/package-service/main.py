import json
import os
import uuid

import httpx
import redis
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest
from starlette.requests import Request

from database import Base, SessionLocal, engine
from models import Package

USUARIO_SERVICE_URL = os.getenv("USUARIO_SERVICE_URL", "http://usuario-service:8000")
TRACKING_SERVICE_URL = os.getenv("TRACKING_SERVICE_URL", "http://tracking-service:8000")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

STATUS_CREATED = "CREATED"

app = FastAPI(title="package-service")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

REQUEST_COUNT = Counter(
    "package_requests_total", "Total HTTP requests in package-service", ["endpoint", "method"]
)
REQUEST_LATENCY = Histogram(
    "package_request_latency_seconds", "Request latency in package-service", ["endpoint", "method"]
)
HTTP_RESPONSES = Counter(
    "package_http_responses_total",
    "Total HTTP responses in package-service",
    ["endpoint", "method", "status_code"],
)


class CreatePackageRequest(BaseModel):
    user_id: int
    package_title: str = "Sin titulo"
    city: str | None = None
    location: str | None = None


class SyncStatusRequest(BaseModel):
    status: str
    location: str | None = None


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    response = await call_next(request)
    endpoint = request.url.path
    method = request.method
    HTTP_RESPONSES.labels(
        endpoint=endpoint,
        method=method,
        status_code=str(response.status_code),
    ).inc()
    return response


def make_tracking_code() -> str:
    return f"TRK-{uuid.uuid4().hex[:12].upper()}"


@app.post("/createPackage")
async def create_package(payload: CreatePackageRequest):
    REQUEST_COUNT.labels(endpoint="/createPackage", method="POST").inc()
    with REQUEST_LATENCY.labels(endpoint="/createPackage", method="POST").time():
        async with httpx.AsyncClient(timeout=5.0) as client:
            user_res = await client.get(f"{USUARIO_SERVICE_URL}/users/{payload.user_id}")
            if user_res.status_code != 200:
                raise HTTPException(status_code=404, detail="user not found")

        db = SessionLocal()
        try:
            code = make_tracking_code()
            record = Package(
                user_id=payload.user_id,
                tracking_code=code,
                package_title=payload.package_title,
                city=payload.city or "",
                location=payload.location or payload.city or "ORIGEN",
                current_status=STATUS_CREATED,
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            async with httpx.AsyncClient(timeout=5.0) as client:
                init_payload = {
                    "tracking_code": code,
                    "user_id": payload.user_id,
                    "status": STATUS_CREATED,
                    "location": record.location,
                    "note": "Paquete registrado",
                }
                init_res = await client.post(
                    f"{TRACKING_SERVICE_URL}/internal/initTracking", json=init_payload
                )
                if init_res.status_code >= 400:
                    db.delete(record)
                    db.commit()
                    raise HTTPException(status_code=502, detail="tracking init failed")

            redis_client.publish(
                "tracking_events",
                json.dumps({
                    "type": "package_created",
                    "tracking_code": code,
                    "user_id": payload.user_id,
                }),
            )

            return {"ok": True, "tracking_code": code, "status": record.current_status, "id": record.id}
        except HTTPException:
            raise
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail="error creating package") from exc
        finally:
            db.close()


@app.get("/getAllPackages")
def get_all_packages():
    REQUEST_COUNT.labels(endpoint="/getAllPackages", method="GET").inc()
    with REQUEST_LATENCY.labels(endpoint="/getAllPackages", method="GET").time():
        db = SessionLocal()
        try:
            rows = db.query(Package).all()
            return [
                {
                    "tracking_code": r.tracking_code,
                    "status": r.current_status,
                    "package_title": r.package_title,
                    "location": r.location,
                    "user_id": r.user_id,
                }
                for r in rows
            ]
        finally:
            db.close()


@app.get("/packages/{tracking_code}")
def get_package_by_tracking(tracking_code: str):
    db = SessionLocal()
    try:
        pkg = db.query(Package).filter(Package.tracking_code == tracking_code).first()
        if not pkg:
            raise HTTPException(status_code=404, detail="not found")
        return {
            "tracking_code": pkg.tracking_code,
            "user_id": pkg.user_id,
            "status": pkg.current_status,
            "package_title": pkg.package_title,
            "location": pkg.location,
        }
    finally:
        db.close()


@app.post("/packages/{tracking_code}/sync-status")
def sync_status(tracking_code: str, payload: SyncStatusRequest):
    db = SessionLocal()
    try:
        pkg = db.query(Package).filter(Package.tracking_code == tracking_code).first()
        if not pkg:
            raise HTTPException(status_code=404, detail="not found")
        pkg.current_status = payload.status
        if payload.location:
            pkg.location = payload.location
        db.commit()
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="sync failed") from exc
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "up", "service": "package-service"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain; version=0.0.4")
