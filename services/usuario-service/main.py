from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest

from database import Base, SessionLocal, engine
from models import User

app = FastAPI(title="usuario-service")

REQUEST_COUNT = Counter(
    "usuario_requests_total", "Total HTTP requests in usuario-service", ["endpoint", "method"]
)
REQUEST_LATENCY = Histogram(
    "usuario_request_latency_seconds", "Request latency in usuario-service", ["endpoint", "method"]
)


class CreateUserRequest(BaseModel):
    username: str
    email: str


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.post("/createUser")
def create_user(payload: CreateUserRequest):
    REQUEST_COUNT.labels(endpoint="/createUser", method="POST").inc()
    with REQUEST_LATENCY.labels(endpoint="/createUser", method="POST").time():
        db = SessionLocal()
        try:
            user = User(username=payload.username.strip(), email=payload.email)
            db.add(user)
            db.commit()
            db.refresh(user)
            return {"ok": True, "user_id": user.id, "username": user.username}
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail="error creating user") from exc
        finally:
            db.close()


@app.get("/getUsers")
def get_users():
    REQUEST_COUNT.labels(endpoint="/getUsers", method="GET").inc()
    with REQUEST_LATENCY.labels(endpoint="/getUsers", method="GET").time():
        db = SessionLocal()
        try:
            users = db.query(User).all()
            return [{"id": u.id, "username": u.username, "email": u.email} for u in users]
        finally:
            db.close()


@app.get("/users/{user_id}")
def get_user_by_id(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="user not found")
        return {"id": user.id, "username": user.username, "email": user.email}
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "up", "service": "usuario-service"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain; version=0.0.4")
