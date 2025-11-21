# ------------------------------------------------------------
# 🧱 Stage 1: Build Tailwind CSS
# ------------------------------------------------------------
FROM node:22-alpine AS frontend

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY tailwind.config.js postcss.config.js ./
COPY suborbit/templates ./suborbit/templates
COPY suborbit/static ./suborbit/static

RUN npx tailwindcss -i ./suborbit/static/src/input.css -o ./suborbit/static/css/tailwind.css --minify

RUN echo "✅ Tailwind CSS built successfully at $(date)"


# ------------------------------------------------------------
# 🐍 Stage 2: Build Python backend
# ------------------------------------------------------------
FROM python:3.12-slim AS backend

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    APP_HOME=/app

WORKDIR $APP_HOME

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python app
COPY suborbit ./suborbit

# Copy compiled CSS from frontend stage
COPY --from=frontend /app/suborbit/static/css ./suborbit/static/css

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "suborbit.app:app"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/healthz')"


ARG APP_VERSION=dev
ENV APP_VERSION=$APP_VERSION
ARG BUILD_DATE=unspecified
ENV BUILD_DATE=${BUILD_DATE}

LABEL org.opencontainers.image.title="SubOrbit"
LABEL org.opencontainers.image.description="Movie discovery app with subtitles, Radarr & Trakt integration."
LABEL org.opencontainers.image.version=$APP_VERSION
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.url="https://github.com/velinea/suborbit"
LABEL io.unraid.docker.icon="https://raw.githubusercontent.com/velinea/suborbit/main/suborbit/static/octopus_logo.png"

