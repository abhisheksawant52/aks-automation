# Slim single-stage image that packages the `aks` CLI.
FROM python:3.12-slim

# Do not write .pyc files or buffer stdout/stderr.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install the package first (better layer caching).
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --upgrade pip && pip install .

# Run as an unprivileged user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

ENTRYPOINT ["aks"]
CMD ["--help"]
