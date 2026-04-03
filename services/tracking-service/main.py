import json
import os

import httpx
import redis
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest

from database import Base, SessionLocal, engine
from models import TrackingEvent

PACKAGE_SERVICE_URL = os.getenv("PACKAGE_SERVICE_URL", "http://package-service:8000")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

STATUS_CREATED = "CREATED"
STATUS_IN_TRANSIT = "IN_TRANSIT"
STATUS_OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
STATUS_DELIVERED = "DELIVERED"
STATUS_EXCEPTION = "EXCEPTION"
ALL_STATUSES = {
    STATUS_CREATED,
    STATUS_IN_TRANSIT,
    STATUS_OUT_FOR_DELIVERY,
    STATUS_DELIVERED,
    STATUS_EXCEPTION,
}

app = FastAPI(title="tracking-service")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

REQUEST_COUNT = Counter(
    "tracking_requests_total", "Total HTTP requests in tracking-service", ["endpoint", "method"]
)
REQUEST_LATENCY = Histogram(
    "tracking_request_latency_seconds", "Request latency in tracking-service", ["endpoint", "method"]
)


class InitTrackingRequest(BaseModel):
    tracking_code: str
    user_id: int | None = None
    status: str = STATUS_CREATED
    location: str | None = None
    note: str | None = None


class UpdateStatusRequest(BaseModel):
    tracking_code: str
    new_status: str | None = None
    status: str | None = None
    location: str | None = None
    note: str | None = None


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.post("/internal/initTracking")
def init_tracking(payload: InitTrackingRequest):
    db = SessionLocal()
    try:
        event = TrackingEvent(
            tracking_code=payload.tracking_code,
            user_id=payload.user_id,
            status=payload.status,
            location=payload.location or "ORIGEN",
            event_note=payload.note or "Paquete registrado",
        )
        db.add(event)
        db.commit()
        return {"ok": True}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="init tracking failed") from exc
    finally:
        db.close()


@app.post("/updateStatus")
async def update_status(payload: UpdateStatusRequest):
    REQUEST_COUNT.labels(endpoint="/updateStatus", method="POST").inc()
    with REQUEST_LATENCY.labels(endpoint="/updateStatus", method="POST").time():
        status = (payload.new_status or payload.status or "").upper()
        if not payload.tracking_code or not status:
            raise HTTPException(status_code=400, detail="bad input")
        if status not in ALL_STATUSES:
            raise HTTPException(status_code=400, detail="invalid status")

        async with httpx.AsyncClient(timeout=5.0) as client:
            pkg_res = await client.get(f"{PACKAGE_SERVICE_URL}/packages/{payload.tracking_code}")
            if pkg_res.status_code != 200:
                raise HTTPException(status_code=404, detail="tracking not found")

        db = SessionLocal()
        try:
            last = (
                db.query(TrackingEvent)
                .filter(TrackingEvent.tracking_code == payload.tracking_code)
                .order_by(TrackingEvent.id.desc())
                .first()
            )
            event = TrackingEvent(
                tracking_code=payload.tracking_code,
                user_id=last.user_id if last else None,
                status=status,
                location=payload.location or (last.location if last else ""),
                event_note=payload.note or f"Cambio de estado a {status}",
            )
            db.add(event)
            db.commit()
            db.refresh(event)

            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{PACKAGE_SERVICE_URL}/packages/{payload.tracking_code}/sync-status",
                    json={"status": status, "location": event.location},
                )

            redis_client.publish(
                "tracking_events",
                json.dumps(
                    {
                        "type": "status_updated",
                        "tracking_code": payload.tracking_code,
                        "status": status,
                        "location": event.location,
                    }
                ),
            )
            return {"ok": True, "tracking_code": payload.tracking_code, "status": status}
        except HTTPException:
            raise
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail="status update failed") from exc
        finally:
            db.close()


@app.get("/getTracking/{tracking_code}")
def get_tracking(tracking_code: str):
    REQUEST_COUNT.labels(endpoint="/getTracking", method="GET").inc()
    with REQUEST_LATENCY.labels(endpoint="/getTracking", method="GET").time():
        db = SessionLocal()
        try:
            rows = (
                db.query(TrackingEvent)
                .filter(TrackingEvent.tracking_code == tracking_code)
                .order_by(TrackingEvent.id.asc())
                .all()
            )
            if not rows:
                raise HTTPException(status_code=404, detail="not found")

            events = [
                {
                    "status": r.status,
                    "location": r.location,
                    "note": r.event_note,
                    "at": r.recorded_at.isoformat() if r.recorded_at else None,
                }
                for r in rows
            ]
            return {
                "tracking_code": tracking_code,
                "current_status": rows[-1].status,
                "events": events,
            }
        finally:
            db.close()


@app.get("/health")
def health():
    return {"status": "up", "service": "tracking-service"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain; version=0.0.4")
