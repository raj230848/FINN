FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY backend/requirements.lock.txt ./requirements.lock.txt
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY backend/app ./app
COPY backend/data/primary ./data/primary
COPY backend/data/nse-directory.json ./data/nse-directory.json
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
