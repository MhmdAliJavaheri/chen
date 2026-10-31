# Dockerfile for Tamper‑Proof Audit Vault (Pure Django)

# Use official lightweight Python image
FROM python:3.11-slim

# Set environment variables for safety
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies (psycopg2 requires libpq-dev and gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create a non‑root user for running the app
RUN useradd --create-home appuser
WORKDIR /app

# Copy only the requirements file first for caching layers
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project source code
COPY . /app/

# Switch to non‑root user
USER appuser

# Wait for the database to be ready (simple script using netcat)
COPY wait_for_db.sh /app/wait_for_db.sh
RUN chmod +x /app/wait_for_db.sh

# Default command runs migrations, then starts the development server
CMD ["/bin/bash", "-c", "./wait_for_db.sh && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
