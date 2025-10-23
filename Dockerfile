# Use a slim Python base image
FROM python:3.11-slim

# Create working dir
WORKDIR /app

# Install system deps (curl useful for debugging)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source into container
COPY src/ /app/

# Ensure /config exists for logs/cache/.env
RUN mkdir -p /config

# Expose web UI port
EXPOSE 5000

# Run Flask app (app.py defines app = Flask(...))
CMD ["python", "app.py"]
