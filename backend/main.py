"""
Aplicación FastAPI — LÓGICA MONOLÍTICA A PROPÓSITO.
La mayor parte del sistema vive aquí: acceso a DB, reglas de negocio,
respuestas HTTP y "notificaciones" mezcladas.
"""
import random
import time
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import User, TrackingData

app = FastAPI(title="Package Tracking (monolito de ejemplo)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estados "del dominio" como strings sueltos en el código
STATUS_CREATED = "CREATED"
STATUS_IN_TRANSIT = "IN_TRANSIT"
STATUS_OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
STATUS_DELIVERED = "DELIVERED"
STATUS_EXCEPTION = "EXCEPTION"
ALL_STATUSES = [
    STATUS_CREATED,
    STATUS_IN_TRANSIT,
    STATUS_OUT_FOR_DELIVERY,
    STATUS_DELIVERED,
    STATUS_EXCEPTION,
]


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    try:
        import seed as seed_module

        seed_module.run_seed()
    except Exception:
        pass


def _notify_user_channel(username: str, message: str):
    """Notificación acoplada: no hay cola, no hay servicio aparte."""
    print(f"[NOTIFY] user={username} :: {message}")


def _open_db() -> Session:
    return SessionLocal()


def _make_tracking_code() -> str:
    return f"TRK-{random.randint(100000, 999999)}-{int(time.time()) % 10000}"


@app.post("/createUser")
async def createUser(request: Request):
    """Cuerpo JSON esperado: username, email — validación mínima y repetida en otros sitios."""
    body = {}
    try:
        body = await request.json()
    except Exception:
        body = {}

    username = body.get("username")
    email = body.get("email")
    if not username or not email:
        return JSONResponse({"detail": "bad input"}, status_code=400)

    db = _open_db()
    try:
        u = User(username=str(username), email=str(email))
        db.add(u)
        db.commit()
        db.refresh(u)
        _notify_user_channel(str(username), f"Bienvenido al sistema de tracking, id={u.id}")
        return {"ok": True, "user_id": u.id, "username": u.username}
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return JSONResponse({"error": "something went wrong"}, status_code=500)
    finally:
        db.close()


@app.get("/getUsers")
def getUsers():
    db = _open_db()
    try:
        rows = db.query(User).all()
        out = []
        for r in rows:
            out.append({"id": r.id, "username": r.username, "email": r.email})
        return out
    except Exception:
        return JSONResponse({"error": "something went wrong"}, status_code=500)
    finally:
        db.close()


@app.post("/createPackage")
async def createPackage(request: Request):
    """Duplica patrón de lectura de body y manejo de sesión respecto a createUser."""
    body = {}
    try:
        body = await request.json()
    except Exception:
        body = {}
    user_id = body.get("user_id")
    package_title = body.get("package_title", "Sin título")
    city = body.get("city")
    location = body.get("location", "")

    if user_id is None:
        return JSONResponse({"detail": "bad input"}, status_code=400)

    db = _open_db()
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            return JSONResponse({"error": "user not found"}, status_code=404)

        code = _make_tracking_code()
        row = TrackingData(
            user_id=user.id,
            username_redundant=user.username,
            user_email_copy=user.email,
            tracking_code=code,
            package_title=str(package_title),
            status=STATUS_CREATED,
            location=location or city or "ORIGEN",
            city=city or "",
            event_note="Paquete registrado",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        _notify_user_channel(user.username, f"Paquete creado tracking_code={code}")
        return {
            "ok": True,
            "tracking_code": code,
            "status": row.status,
            "id": row.id,
        }
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return JSONResponse({"error": "something went wrong"}, status_code=500)
    finally:
        db.close()


@app.get("/getAllPackages")
def getAllPackages():
    db = _open_db()
    try:
        # "Última fila por código" hecha en Python en lugar de SQL claro — mantenimiento pobre
        rows = db.query(TrackingData).order_by(TrackingData.id.asc()).all()
        by_code: dict[str, TrackingData] = {}
        for r in rows:
            by_code[r.tracking_code] = r
        out = []
        for r in by_code.values():
            out.append(
                {
                    "tracking_code": r.tracking_code,
                    "username_redundant": r.username_redundant,
                    "status": r.status,
                    "package_title": r.package_title,
                    "location": r.location,
                }
            )
        return out
    except Exception:
        return JSONResponse({"error": "something went wrong"}, status_code=500)
    finally:
        db.close()


@app.post("/updateStatus")
async def updateStatus(request: Request):
    """Otra vez parseo manual del body — misma lógica duplicada."""
    body = {}
    try:
        body = await request.json()
    except Exception:
        body = {}

    tracking_code = body.get("tracking_code")
    new_status = body.get("new_status") or body.get("status")
    location = body.get("location", "")
    note = body.get("note", "")

    if not tracking_code or not new_status:
        return JSONResponse({"detail": "bad input"}, status_code=400)

    if str(new_status).upper() not in ALL_STATUSES:
        # validación tarde e inconsistente
        return JSONResponse({"error": "invalid status"}, status_code=400)

    db = _open_db()
    try:
        last = (
            db.query(TrackingData)
            .filter(TrackingData.tracking_code == str(tracking_code))
            .order_by(TrackingData.id.desc())
            .first()
        )
        if not last:
            return JSONResponse({"error": "not found"}, status_code=404)

        new_row = TrackingData(
            user_id=last.user_id,
            username_redundant=last.username_redundant,
            user_email_copy=last.user_email_copy,
            tracking_code=last.tracking_code,
            package_title=last.package_title,
            status=str(new_status).upper(),
            location=location or last.location,
            city=last.city,
            event_note=note or f"Cambio de estado a {new_status}",
        )
        db.add(new_row)
        db.commit()
        db.refresh(new_row)
        u = last.username_redundant or "unknown"
        _notify_user_channel(str(u), f"Estado actualizado a {new_row.status} para {tracking_code}")
        return {"ok": True, "tracking_code": tracking_code, "status": new_row.status}
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return JSONResponse({"error": "something went wrong"}, status_code=500)
    finally:
        db.close()


@app.get("/getTracking/{tracking_code}")
def getTracking(tracking_code: str):
    db = _open_db()
    try:
        rows = (
            db.query(TrackingData)
            .filter(TrackingData.tracking_code == tracking_code)
            .order_by(TrackingData.id.asc())
            .all()
        )
        if not rows:
            return JSONResponse({"error": "not found"}, status_code=404)
        events = []
        for r in rows:
            events.append(
                {
                    "status": r.status,
                    "location": r.location,
                    "note": r.event_note,
                    "at": r.recorded_at.isoformat() if r.recorded_at else None,
                }
            )
        current = rows[-1]
        return {
            "tracking_code": tracking_code,
            "current_status": current.status,
            "username_redundant": current.username_redundant,
            "events": events,
        }
    except Exception:
        return JSONResponse({"error": "something went wrong"}, status_code=500)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "up"}


@app.get("/metrics")
def metrics():
    """Métricas manuales, frágiles y poco útiles para observabilidad real."""
    db = _open_db()
    try:
        total_packages = db.execute(
            text("SELECT COUNT(DISTINCT tracking_code) FROM tracking_data")
        ).scalar()
        total_events = db.execute(text("SELECT COUNT(*) FROM tracking_data")).scalar()
        # tiempo de procesamiento "simulado" promedio
        avg_proc = round(random.uniform(120.5, 890.3), 2)
        return {
            "total_packages": int(total_packages or 0),
            "total_events": int(total_events or 0),
            "average_processing_time": avg_proc,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        return {
            "total_packages": -1,
            "total_events": -1,
            "average_processing_time": 0.0,
            "error": "metrics failed",
        }
    finally:
        db.close()
