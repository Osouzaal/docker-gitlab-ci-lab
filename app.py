"""Aplicação mínima usada para demonstrar o pipeline Docker + GitLab CI/CD.

Endpoints:
  GET  /             informações do app e a versão (commit) em execução
  GET  /api/health   usado pelo healthcheck do Docker
  GET  /api/visits   lê o contador de visitas
  POST /api/visits   incrementa o contador (grava em arquivo, no volume)
"""
import json
import os
import threading

from flask import Flask, jsonify

app = Flask(__name__)

DATA_PATH = os.environ.get("DATA_PATH") or os.path.join(os.path.dirname(__file__), "data.json")
APP_VERSION = os.environ.get("APP_VERSION", "dev")

# O contador é um arquivo JSON sem controle de concorrência entre processos.
# Por isso o Gunicorn roda com 1 worker; as threads dividem este lock.
_lock = threading.Lock()


def _load() -> dict:
    try:
        with open(DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"visits": 0}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    tmp = DATA_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, DATA_PATH)  # troca atômica: nunca deixa o arquivo pela metade


@app.get("/")
def index():
    return jsonify(
        app="docker-gitlab-ci-lab",
        version=APP_VERSION,
        endpoints=["GET /api/health", "GET /api/visits", "POST /api/visits"],
    )


@app.get("/api/health")
def health():
    return jsonify(status="ok")


@app.get("/api/visits")
def get_visits():
    with _lock:
        return jsonify(visits=_load()["visits"])


@app.post("/api/visits")
def add_visit():
    with _lock:
        data = _load()
        data["visits"] += 1
        _save(data)
        return jsonify(visits=data["visits"])
