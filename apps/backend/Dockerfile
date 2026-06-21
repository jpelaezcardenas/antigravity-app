# Dockerfile for Contexia Backend
# Single-stage: all Python deps ship as prebuilt wheels (psycopg2-binary,
# cryptography, bcrypt), so NO compiler/build-essential is needed.

FROM python:3.11-slim

WORKDIR /app

# Minimal tooling: curl+unzip only to fetch the Bitwarden CLI binary.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Bitwarden CLI (native linux binary, no Node.js required).
# Best-effort: if the download fails the build still succeeds; the secrets
# health endpoint will simply report "unhealthy" until bw is available.
RUN curl -fsSL "https://vault.bitwarden.com/download/?app=cli&platform=linux" -o /tmp/bw.zip \
    && unzip /tmp/bw.zip -d /usr/local/bin \
    && chmod +x /usr/local/bin/bw \
    && rm /tmp/bw.zip \
    || echo "WARNING: Bitwarden CLI install failed; /api/v1/secrets/health will report unhealthy"

# Python dependencies (all wheels — fast, no compilation)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Run with uvicorn (supports dynamic PORT environment variable)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers"]
