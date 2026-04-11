FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/prod.txt /app/requirements/
COPY requirements/base.in requirements/prod.in /app/requirements/

RUN pip install --no-cache-dir --timeout 120 -r /app/requirements/prod.txt

COPY . /app
RUN chmod +x /app/docker/entrypoint.sh

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "-c", "docker/gunicorn.conf.py", "config.wsgi:application"]
