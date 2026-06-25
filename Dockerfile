# Stage 1: Builder — install dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir "poetry>=2.0.0,<3.0.0"

COPY pyproject.toml poetry.lock ./

# Install dependencies (including torch from PyPI — no force-reinstall needed)
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root

# Install CPU-only PyTorch in-place (much smaller binary, avoids CUDA lib conflicts)
# This replaces the CUDA torch that Poetry installed from PyPI
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        "torch>=2.0.0,<3.0.0" --force-reinstall --no-deps


# Stage 2: Runtime — minimal final image
FROM python:3.12-slim

WORKDIR /app

# Copy only the site-packages we need (use --chown to avoid extra layer)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]