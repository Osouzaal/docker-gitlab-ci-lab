FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_PATH=/data/data.json

ARG APP_VERSION=dev
ENV APP_VERSION=$APP_VERSION

WORKDIR /app

# Dependências antes do código: o Docker reaproveita esta camada do cache
COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn==23.0.0

# Usuário sem privilégios e pasta de dados (vira volume)
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /data \
    && chown app:app /data

COPY --chown=app:app . .

USER app
EXPOSE 8080
VOLUME ["/data"]

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=4)" || exit 1

# 1 worker: o contador é um arquivo sem trava entre processos
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--access-logfile", "-", "app:app"]
