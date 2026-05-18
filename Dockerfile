# Dockerfile para a aplicacao Django (Foundation F-A em diante).
# Imagem base alinhada com .devcontainer/devcontainer.json (Python 3.12 bookworm).

FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.8.3

# Pacotes do sistema necessarios pro psycopg + build de extensoes nativas
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /app

# Camada de cache de dependencias (so reinvalida quando pyproject muda)
# F-A em diante: instala dev tambem (pytest, django-extensions etc). Deploy
# autorizado pelo Roldao vai introduzir multi-stage com --without dev.
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root

# Codigo da aplicacao
COPY . .

# Usuario nao-root pra rodar a app (defesa em profundidade)
RUN groupadd --system app && useradd --system --gid app --home /app app \
    && chown -R app:app /app
USER app

EXPOSE 8000

# Default: producao com gunicorn (dev override pelo docker-compose com runserver)
CMD ["poetry", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
