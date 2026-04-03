# Sistema de Tracking de Paquetes

Repositorio academico para evolucion de arquitectura desde un monolito hacia una solucion de microservicios con observabilidad.

## 1) Estado actual del proyecto

El repositorio mantiene dos enfoques:

- Monolito de practica (legado): implementado en `backend/` para analisis AS-IS y comparacion.
- Arquitectura de microservicios (TO-BE): implementada y operativa con gateway, servicios independientes y base de datos por dominio.

## 2) Arquitectura de microservicios implementada

Servicios y responsabilidades:

- `usuario-service`: creacion y consulta de usuarios.
- `package-service`: registro de paquetes y orquestacion inicial de tracking.
- `tracking-service`: historial de eventos y actualizacion de estado.
- `notification-service`: consumo de eventos y notificaciones asincronas basicas.
- `api-gateway` (Nginx): punto unico de entrada para frontend y clientes.

Persistencia por servicio:

- `usuario-db` (PostgreSQL): datos de usuarios.
- `package-db` (PostgreSQL): datos de paquetes.
- `tracking-db` (PostgreSQL): eventos de tracking.

Infraestructura complementaria:

- Redis (Pub/Sub) para eventos entre servicios.
- Prometheus para scraping de metricas.
- Grafana para visualizacion.
- Postgres Exporter para metricas de base de datos.

## 3) Funcionalidades nuevas implementadas

Implementadas sobre la arquitectura de microservicios:

- Separacion de dominios en servicios independientes.
- Base de datos dedicada por microservicio (aislamiento de datos).
- API Gateway con rutas unificadas para compatibilidad funcional.
- Swagger por microservicio (`/docs` en puertos individuales).
- Flujo E2E distribuido:
	- Crear usuario.
	- Crear paquete para usuario.
	- Inicializar tracking en servicio de tracking.
	- Actualizar estado y registrar historial.
- Publicacion de eventos en Redis (`tracking_events`).
- Servicio de notificaciones suscrito a eventos.
- Endpoints de salud y metricas por servicio (`/health`, `/metrics`).
- CORS habilitado en gateway para frontend en distinto origen.

## 4) Endpoints de negocio expuestos por gateway

Base URL: `http://localhost:8000`

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/createUser` | Crea usuario (`username`, `email`) |
| GET | `/getUsers` | Lista usuarios |
| POST | `/createPackage` | Crea paquete (`user_id`, `package_title`, `city`, `location`) |
| GET | `/getAllPackages` | Lista paquetes con estado actual |
| POST | `/updateStatus` | Actualiza estado de tracking |
| GET | `/getTracking/{tracking_code}` | Retorna historial + estado actual |
| GET | `/health` | Salud del sistema (gateway -> usuario-service) |
| GET | `/metrics` | Metricas expuestas por servicio de usuarios |

Estados validos de tracking:

- `CREATED`
- `IN_TRANSIT`
- `OUT_FOR_DELIVERY`
- `DELIVERED`
- `EXCEPTION`

## 5) Swagger / OpenAPI

Swagger por microservicio:

- `http://localhost:8001/docs` -> usuario-service
- `http://localhost:8002/docs` -> package-service
- `http://localhost:8003/docs` -> tracking-service
- `http://localhost:8004/docs` -> notification-service

OpenAPI JSON:

- `http://localhost:8001/openapi.json`
- `http://localhost:8002/openapi.json`
- `http://localhost:8003/openapi.json`
- `http://localhost:8004/openapi.json`

## 6) Ejecucion del proyecto

Requisitos:

- Docker
- Docker Compose

Levantar stack completo:

```bash
docker compose up --build
```

Accesos principales:

- Frontend: `http://localhost:8080`
- API Gateway: `http://localhost:8000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## 7) Entorno local Python (opcional)

Para ejecutar servicios fuera de Docker:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.local.txt
```

`requirements.local.txt` centraliza dependencias de `backend/` y `services/`.

## 8) Documentacion adicional

- Informe tecnico de migracion: `docs/informe_hito1.md`
- Implementacion de microservicios (resumen tecnico): `docs/implementacion_microservicios.md`

## 9) Nota academica

El monolito legado se conserva con fines de analisis de deuda tecnica y comparacion AS-IS vs TO-BE.
