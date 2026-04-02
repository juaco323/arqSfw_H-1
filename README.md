# Sistema de Tracking de Paquetes (monolito de práctica)

API monolítica **funcional** pero **mal diseñada a propósito**, para cursos de arquitectura, refactor y evolución hacia microservicios.

## Estructura del repositorio

- `backend/` — FastAPI, SQLAlchemy, Docker propio (`Dockerfile`), semilla y esquema SQL de referencia.
- `frontend/` — Vue 3 + Vite (UI de ejemplo, también con malas prácticas a propósito).
- `docker-compose.yml` — en la raíz: levanta **postgres**, **backend** y **frontend**.

## Requisitos

- Docker y Docker Compose

## Ejecutar todo el stack

```bash
docker compose up --build
```

- API: `http://localhost:8000` (documentación: `/docs`).
- UI (Nginx): `http://localhost:8080`.

Desarrollo del front sin Docker: `cd frontend && npm install && npm run dev` → `http://localhost:5173`. El backend expone CORS abierto para URLs absolutas desde el navegador durante el curso.

Desarrollo del backend sin Docker: `cd backend`, entorno virtual, `pip install -r requirements.txt`, variables `DB_*` apuntando a tu PostgreSQL, y `uvicorn main:app --reload`.

## Endpoints (nombres no REST a propósito)

| Método | Ruta | Descripción breve |
|--------|------|-------------------|
| POST | `/createUser` | Crear usuario (`username`, `email`) |
| GET | `/getUsers` | Listar usuarios |
| POST | `/createPackage` | Crear envío (`user_id`, `package_title`, opcionales `city`, `location`) |
| GET | `/getAllPackages` | Listar último estado por `tracking_code` |
| POST | `/updateStatus` | Nuevo evento (`tracking_code`, `new_status`, opcionales `location`, `note`) |
| GET | `/getTracking/{tracking_code}` | Historial y estado actual |
| GET | `/health` | Salud mínima |
| GET | `/metrics` | `total_packages`, `total_events`, `average_processing_time` (valor simulado), timestamps |

Estados válidos para `updateStatus`: `CREATED`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`, `DELIVERED`, `EXCEPTION`.

El archivo `backend/schema_mal_diseno.sql` describe en SQL el mismo esquema denormalizado (solo referencia; la app usa `Base.metadata.create_all`).

## Datos de prueba

Al levantar con bases vacías, el arranque intenta ejecutar la semilla (`backend/seed.py`): 3 usuarios y paquetes `TRK-SEED-1001`, `TRK-SEED-2002`, `TRK-SEED-3003`.

Semilla manual:

```bash
docker compose exec backend python seed.py
```

## Variables de entorno (backend)

| Variable | Ejemplo | Uso |
|----------|---------|-----|
| `DB_HOST` | `postgres` | Host PostgreSQL |
| `DB_PORT` | `5432` | Puerto |
| `DB_USER` | `tracker` | Usuario |
| `DB_PASSWORD` | `tracker_secret` | Contraseña |
| `DB_NAME` | `package_tracking` | Base de datos |

## Advertencia pedagógica

Este repositorio incorpora de forma intencional: acoplamiento alto, tabla denormalizada, duplicación de lógica, rutas inconsistentes, manejo de errores pobre y observabilidad débil. **No** usar como referencia de buenas prácticas.
