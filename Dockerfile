# ── Stage 1: dependencies ─────────────────────────────────────────────────────
FROM python:3.13-slim AS deps

WORKDIR /app

# Install dependencies in an isolated layer so they're cached unless
# requirements.txt changes — keeps rebuild times fast.
COPY requirements.txt .
RUN pip install --upgrade pip --quiet \
    && pip install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

# Non-root user — never run app code as root in a container
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Copy installed packages from the deps stage
COPY --from=deps /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application source
COPY app/ ./app/
COPY run.py .

# Own everything as the app user
RUN chown -R app:app /app

USER app

# Unbuffered output so logs stream immediately to Docker / stdout
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Use uvicorn directly — no shell wrapper, PID 1 gets signals correctly
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
