# SmartCart Bot Service Dockerfile
# Note: Keep ports in sync with config/ports.yaml (smartcart-bot: containerPort 8087)

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
		PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
		curl ca-certificates && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY smartcart_bot ./smartcart_bot

EXPOSE 8087

# Health check (optional; actual k8s probes should hit /health)
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
	CMD curl -fsS http://localhost:8087/health || exit 1

CMD ["uvicorn", "smartcart_bot.main:app", "--host", "0.0.0.0", "--port", "8087"]
