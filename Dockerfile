# ── Stage 1: Build React frontend ──────────────────────────────────────────
FROM node:22-slim AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python app ─────────────────────────────────────────────────────
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

# Copy built frontend dist
COPY --from=frontend-build /frontend/dist ./frontend/dist

EXPOSE 8080

CMD ["python", "main.py"]