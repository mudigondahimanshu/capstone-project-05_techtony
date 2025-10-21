FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# ✅ add PyTorch CPU wheels
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY server/ ./server/

# Cloud Run uses $PORT
ENV PORT=8080
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8080"]
