# Build trained artifacts once into the image; runtime startup never retrains models.
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY team3-ml-simulation ./team3-ml-simulation
ENV PYTHONUTF8=1 ML_N_JOBS=1
RUN python team3-ml-simulation/train_models.py

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/team2-backend:/app/team3-ml-simulation
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY team1-frontend ./team1-frontend
COPY team2-backend ./team2-backend
COPY team3-ml-simulation ./team3-ml-simulation
COPY --from=builder /app/team3-ml-simulation/models ./team3-ml-simulation/models
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "team2-backend", "--host", "0.0.0.0", "--port", "8000"]
