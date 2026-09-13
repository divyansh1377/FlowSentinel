# FlowSentinel - Team 2 Backend Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy root requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source trees
COPY team2-backend /app/team2-backend
COPY team3-ml-simulation /app/team3-ml-simulation
COPY team1-frontend /app/team1-frontend
COPY API_CONTRACT.md /app/API_CONTRACT.md

WORKDIR /app/team2-backend

EXPOSE 8000

ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=False

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

