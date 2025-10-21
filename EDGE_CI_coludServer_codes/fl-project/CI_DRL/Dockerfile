FROM python:3.10-slim
WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add your DRL code + helper scripts
COPY . .

# Default: just print help. EDGE will override CMD in their orchestrator, or call python scripts directly.
CMD ["python", "-c", "print('client image ready. Set CMD to run training and client_uploader.py')"]
