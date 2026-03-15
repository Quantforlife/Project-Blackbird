version: "3.9"

services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    container_name: blackbird_postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-blackbird}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-blackbird_secret}
      POSTGRES_DB: ${POSTGRES_DB:-blackbird}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-blackbird}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: blackbird_redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: blackbird_backend
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-blackbird}:${POSTGRES_PASSWORD:-blackbird_secret}@postgres:5432/${POSTGRES_DB:-blackbird}
      SYNC_DATABASE_URL: postgresql://${POSTGRES_USER:-blackbird}:${POSTGRES_PASSWORD:-blackbird_secret}@postgres:5432/${POSTGRES_DB:-blackbird}
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/1
      CELERY_RESULT_BACKEND: redis://redis:6379/2
      API_KEY: ${API_KEY:-blackbird-alpha-key}
      UPLOAD_DIR: /app/uploads
      DEBUG: ${DEBUG:-true}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - uploads_data:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: blackbird_worker
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-blackbird}:${POSTGRES_PASSWORD:-blackbird_secret}@postgres:5432/${POSTGRES_DB:-blackbird}
      SYNC_DATABASE_URL: postgresql://${POSTGRES_USER:-blackbird}:${POSTGRES_PASSWORD:-blackbird_secret}@postgres:5432/${POSTGRES_DB:-blackbird}
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/1
      CELERY_RESULT_BACKEND: redis://redis:6379/2
      API_KEY: ${API_KEY:-blackbird-alpha-key}
      UPLOAD_DIR: /app/uploads
    volumes:
      - ./backend:/app
      - uploads_data:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2

  simulation:
    build:
      context: ./simulation
      dockerfile: Dockerfile
    container_name: blackbird_simulation
    environment:
      BACKEND_URL: http://backend:8000
      API_KEY: ${API_KEY:-blackbird-alpha-key}
      NUM_DRONES: ${NUM_DRONES:-3}
    volumes:
      - ./simulation:/app
    depends_on:
      - backend
    command: python main.py

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        REACT_APP_API_URL: ${REACT_APP_API_URL:-http://localhost:8000}
        REACT_APP_WS_URL: ${REACT_APP_WS_URL:-ws://localhost:8000}
    container_name: blackbird_frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
  uploads_data:
