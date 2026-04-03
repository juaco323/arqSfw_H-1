# Sistema de Tracking de Paquetes (monolito de practica)

API monolitica funcional pero mal disenada a proposito, para cursos de arquitectura, refactor y evolucion hacia microservicios.

## Estructura del repositorio

- `backend/` - FastAPI, SQLAlchemy, Docker propio (`Dockerfile`), semilla y esquema SQL de referencia.
- `frontend/` - Vue 3 + Vite (UI de ejemplo, tambien con malas practicas a proposito).
- `docker-compose.yml` - en la raiz: levanta postgres, backend y frontend.

## Requisitos

- Docker y Docker Compose

## Entorno local Python (venv)

Para ejecutar backend/servicios fuera de Docker, crear primero un entorno virtual en la raiz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.local.txt
```

El archivo `requirements.local.txt` centraliza dependencias de `backend/` y `services/`.

## Ejecutar todo el stack

```bash
docker compose up --build
```

Notas de portabilidad:

- Los contenedores Python instalan dependencias desde `requirements.txt` de cada servicio.
- El contenedor frontend usa `npm ci` + `package-lock.json` para builds reproducibles en otras maquinas.

- API: `http://localhost:8000` (documentacion: `/docs`).
- UI (Nginx): `http://localhost:8080`.

Desarrollo del front sin Docker: `cd frontend && npm install && npm run dev` -> `http://localhost:5173`.

Desarrollo del backend sin Docker: `cd backend`, entorno virtual, `pip install -r requirements.txt`, variables `DB_*` apuntando a tu PostgreSQL, y `uvicorn main:app --reload`.

## Endpoints (nombres no REST a proposito)

| Metodo | Ruta | Descripcion breve |
|--------|------|-------------------|
| POST | `/createUser` | Crear usuario (`username`, `email`) |
| GET | `/getUsers` | Listar usuarios |
| POST | `/createPackage` | Crear envio (`user_id`, `package_title`, opcionales `city`, `location`) |
| GET | `/getAllPackages` | Listar ultimo estado por `tracking_code` |
| POST | `/updateStatus` | Nuevo evento (`tracking_code`, `new_status`, opcionales `location`, `note`) |
| GET | `/getTracking/{tracking_code}` | Historial y estado actual |
| GET | `/health` | Salud minima |
| GET | `/metrics` | `total_packages`, `total_events`, `average_processing_time` (valor simulado), timestamps |

Estados validos para `updateStatus`: `CREATED`, `IN_TRANSIT`, `OUT_FOR_DELIVERY`, `DELIVERED`, `EXCEPTION`.

El archivo `backend/schema_mal_diseno.sql` describe en SQL el mismo esquema denormalizado (solo referencia; la app usa `Base.metadata.create_all`).

## Datos de prueba

Al levantar con bases vacias, el arranque intenta ejecutar la semilla (`backend/seed.py`): 3 usuarios y paquetes `TRK-SEED-1001`, `TRK-SEED-2002`, `TRK-SEED-3003`.

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
| `DB_PASSWORD` | `tracker_secret` | Contrasena |
| `DB_NAME` | `package_tracking` | Base de datos |

## Advertencia pedagogica

Este repositorio incorpora de forma intencional: acoplamiento alto, tabla denormalizada, duplicacion de logica, rutas inconsistentes, manejo de errores pobre y observabilidad debil. No usar como referencia de buenas practicas.
