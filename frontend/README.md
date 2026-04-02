# Frontend Vue (ejemplo con malas prácticas)

Vue 3 + Vite + JavaScript. Pensado para conectar con el backend FastAPI en `http://localhost:8000`.

Desde la raíz del repositorio, `docker compose up --build` levanta Postgres, el backend (`backend/`) y este frontend en `http://localhost:8080`.

## Desarrollo

```bash
npm install
npm run dev
```

Abre `http://localhost:5173` con el backend ya levantado.

## Build / preview local

```bash
npm run build
npm run preview
```

## Docker (Nginx sirviendo el build estático)

Desde la carpeta `frontend`:

```bash
docker build -t tracking-fe .
docker run -p 8080:80 tracking-fe
```

El navegador seguirá llamando al API en `http://localhost:8000` (CORS debe estar habilitado en el backend).
