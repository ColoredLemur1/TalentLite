FROM python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90

WORKDIR /app

# Production dependencies only. Copied before the code so this layer is cached.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Only the application package: no tests, no .git, and never .env.
COPY app/ ./app/

# The app runs as an unprivileged user. /data belongs to that user, so a new named
# volume mounted there inherits the ownership and the app can write its database.
RUN useradd --system --no-create-home --uid 10001 appuser \
    && mkdir /data \
    && chown appuser:appuser /data
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:build_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
