FROM python:3.11-slim

# Install system dependencies for OpenCV and MediaPipe
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=False

CMD ["python", "app/main.py", "--mode", "web"]
