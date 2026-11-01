# Full Next.js + FastAPI stack, one public port and one persistent database.
FROM node:22-bookworm-slim AS frontend-build
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=frontend-build /usr/local/bin/node /usr/local/bin/node
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY backend/requirements.lock.txt backend/requirements.lock.txt
RUN pip install --no-cache-dir -r backend/requirements.lock.txt
COPY backend/app backend/app
COPY backend/data/primary backend/data/primary
COPY scripts/start_hosted.py scripts/start_hosted.py
COPY --from=frontend-build /build/.next/standalone frontend/.next/standalone
COPY --from=frontend-build /build/.next/static frontend/.next/standalone/.next/static
COPY --from=frontend-build /build/public frontend/.next/standalone/public
RUN useradd --system --user-group --uid 10001 finn && mkdir -p /var/lib/finn && chown -R finn:finn /var/lib/finn /app/backend/data /app/frontend
# The supervisor prepares a newly mounted disk, then drops to finn before launch.
EXPOSE 8080
CMD ["python", "scripts/start_hosted.py"]
