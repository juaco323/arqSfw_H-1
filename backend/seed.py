"""
Datos de prueba — invocados desde startup de main o manualmente:
python seed.py
"""
from database import SessionLocal
from models import User, TrackingData

STATUS_CREATED = "CREATED"
STATUS_IN_TRANSIT = "IN_TRANSIT"
STATUS_OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
STATUS_DELIVERED = "DELIVERED"
STATUS_EXCEPTION = "EXCEPTION"

SEED_MARKER_CODE = "TRK-SEED-1001"


def run_seed():
    db = SessionLocal()
    try:
        if db.query(TrackingData).filter(TrackingData.tracking_code == SEED_MARKER_CODE).first():
            return

        if db.query(User).count() == 0:
            db.add_all(
                [
                    User(username="ana_lopez", email="ana@example.com"),
                    User(username="ben_kim", email="ben@example.com"),
                    User(username="carla_m", email="carla@example.com"),
                ]
            )
            db.commit()

        users = db.query(User).order_by(User.id.asc()).limit(3).all()
        if len(users) < 3:
            return
        u1, u2, u3 = users[0], users[1], users[2]

        def add_events_for_package(
            uid: int,
            uname: str,
            email: str,
            code: str,
            title: str,
            states: list[tuple[str, str, str, str]],
        ):
            for status, loc, city, note in states:
                db.add(
                    TrackingData(
                        user_id=uid,
                        username_redundant=uname,
                        user_email_copy=email,
                        tracking_code=code,
                        package_title=title,
                        status=status,
                        location=loc,
                        city=city,
                        event_note=note,
                    )
                )

        add_events_for_package(
            u1.id,
            u1.username,
            u1.email,
            "TRK-SEED-1001",
            "Libros",
            [
                (STATUS_CREATED, "Bodega Central", "Santiago", "Ingreso"),
                (STATUS_IN_TRANSIT, "Hub Norte", "La Serena", "En ruta"),
                (STATUS_OUT_FOR_DELIVERY, "Camión 12", "La Serena", "Reparto"),
            ],
        )
        add_events_for_package(
            u2.id,
            u2.username,
            u2.email,
            "TRK-SEED-2002",
            "Electrónica",
            [
                (STATUS_CREATED, "CD Valparaíso", "Valparaíso", "Registrado"),
                (STATUS_IN_TRANSIT, "Avión", "SCL", "Tránsito aéreo"),
            ],
        )
        add_events_for_package(
            u3.id,
            u3.username,
            u3.email,
            "TRK-SEED-3003",
            "Regalo",
            [
                (STATUS_CREATED, "Punto pickup", "Concepción", "Creación"),
                (STATUS_EXCEPTION, "Centro excepciones", "Concepción", "Demora aduanal"),
                (STATUS_IN_TRANSIT, "Reenvío", "Concepción", "Recuperado"),
                (STATUS_DELIVERED, "Domicilio", "Concepción", "Entregado"),
            ],
        )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    from database import Base, engine

    Base.metadata.create_all(bind=engine)
    run_seed()
    print("Seed aplicado.")
