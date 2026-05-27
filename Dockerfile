# Dockerfile para a aplicacao Django (Foundation F-A em diante).
# Imagem base alinhada com .devcontainer/devcontainer.json (Python 3.12 bookworm).
#
# SUPPLY-1 pin SHA (Onda PRE-A.4 auditoria 10 lentes pré-Wave A — fecha L8#7 ALTO):
# Dependabot atualiza este SHA semanalmente via .github/dependabot.yml.
# Tag mutável `python:3.12-slim-bookworm` resolvida em 2026-05-27 → SHA pinado abaixo.

FROM python:3.12-slim-bookworm@sha256:5f55cdf0c5d9dc1a415637a5ccc4a9e18663ad203673173b8cda8f8dcacef689

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.8.3

# Pacotes do sistema necessarios pro psycopg + build de extensoes nativas +
# WeasyPrint (Marco 2 T-EQP-002 — TL1 tech-lead):
#   libpango/libcairo/libgdk-pixbuf — renderizacao HTML->PDF
#   fonts-dejavu-core — fonte padrao garantida em container slim
#   shared-mime-info — deteccao de tipos pelas libs Pango/Cairo
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
        shared-mime-info \
        fonts-dejavu-core \
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
