# Implementacion de Microservicios

## Resumen

Este documento describe la implementacion real de la arquitectura TO-BE del sistema de tracking, con servicios independientes y base de datos por dominio.

## Servicios implementados

### 1) usuario-service

Responsabilidad:

- Crear usuarios.
- Consultar usuarios.

Endpoints:

- `POST /createUser`
- `GET /getUsers`
- `GET /users/{user_id}`
- `GET /health`
- `GET /metrics`

Base de datos asociada:

- `usuario-db` (PostgreSQL)

### 2) package-service

Responsabilidad:

- Crear paquetes para usuarios existentes.
- Consultar paquetes.
- Sincronizar estado actual desde tracking-service.

Endpoints:

- `POST /createPackage`
- `GET /getAllPackages`
- `GET /packages/{tracking_code}`
- `POST /packages/{tracking_code}/sync-status`
- `GET /health`
- `GET /metrics`

Base de datos asociada:

- `package-db` (PostgreSQL)

### 3) tracking-service

Responsabilidad:

- Inicializar tracking.
- Actualizar estado de envios.
- Exponer historial y estado actual.

Endpoints:

- `POST /internal/initTracking`
- `POST /updateStatus`
- `GET /getTracking/{tracking_code}`
- `GET /health`
- `GET /metrics`

Base de datos asociada:

- `tracking-db` (PostgreSQL)

### 4) notification-service

Responsabilidad:

- Consumir eventos de Redis y procesar notificaciones basicas.

Endpoints:

- `GET /health`
- `GET /metrics`

Base de datos asociada:

- No aplica (servicio sin BD propia en esta version).

## API Gateway

Componente:

- Nginx (`api-gateway`)

Funciones:

- Punto unico de entrada.
- Enrutamiento a microservicios.
- CORS habilitado para frontend en distinto origen.
- Respuesta de preflight `OPTIONS`.

Rutas expuestas por gateway:

- `POST /createUser`
- `GET /getUsers`
- `POST /createPackage`
- `GET /getAllPackages`
- `POST /updateStatus`
- `GET /getTracking/{tracking_code}`
- `GET /health`
- `GET /metrics`

## Eventos y comunicacion asincrona

Bus de eventos:

- Redis Pub/Sub, canal `tracking_events`.

Eventos publicados:

- `package_created`
- `status_updated`

Publicadores:

- package-service
- tracking-service

Consumidor:

- notification-service

## Observabilidad

Implementado:

- Metricas Prometheus por servicio (`/metrics`).
- Scrape de Prometheus para servicios y postgres-exporter.
- Visualizacion en Grafana.

Puertos:

- Prometheus: `9090`
- Grafana: `3000`

## Swagger por microservicio

- usuario-service: `http://localhost:8001/docs`
- package-service: `http://localhost:8002/docs`
- tracking-service: `http://localhost:8003/docs`
- notification-service: `http://localhost:8004/docs`

## Flujo funcional E2E implementado

1. Crear usuario (`/createUser`).
2. Crear paquete (`/createPackage`).
3. Inicializar tracking (`/internal/initTracking` interno).
4. Actualizar estado (`/updateStatus`).
5. Consultar historial (`/getTracking/{tracking_code}`).

## Despliegue local

```bash
docker compose up --build
```

Entradas principales:

- Frontend: `http://localhost:8080`
- Gateway: `http://localhost:8000`
