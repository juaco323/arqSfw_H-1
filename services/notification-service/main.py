import json
import os
import threading

import redis
from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import Counter, generate_latest

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = FastAPI(title="notification-service")

NOTIFICATIONS_PROCESSED = Counter(
    "notifications_processed_total", "Total notifications processed"
)
NOTIFICATION_ERRORS = Counter(
    "notifications_errors_total", "Total notification processing errors"
)


class NotificationWorker:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._stop = threading.Event()

    def run(self) -> None:
        client = redis.Redis.from_url(self.redis_url, decode_responses=True)
        pubsub = client.pubsub()
        pubsub.subscribe("tracking_events")
        while not self._stop.is_set():
            msg = pubsub.get_message(timeout=1.0)
            if not msg or msg.get("type") != "message":
                continue
            try:
                payload = json.loads(msg["data"])
                print(f"[notification-service] event={payload}")
                NOTIFICATIONS_PROCESSED.inc()
            except Exception:
                NOTIFICATION_ERRORS.inc()

    def stop(self) -> None:
        self._stop.set()


worker = NotificationWorker(REDIS_URL)
thread: threading.Thread | None = None


@app.on_event("startup")
def startup_event() -> None:
    global thread
    thread = threading.Thread(target=worker.run, daemon=True)
    thread.start()


@app.on_event("shutdown")
def shutdown_event() -> None:
    worker.stop()


@app.get("/health")
def health():
    return {"status": "up", "service": "notification-service"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain; version=0.0.4")
