#!/bin/bash
# Cria o banco de teste `test_afere` na inicializacao do volume.
#
# Por que aqui (e nao no test runner):
# - app_user e app_migrator sao NOCREATEDB (ADR-0002 — defesa em
#   profundidade). Sem isso, pytest-django nao consegue criar o test DB.
# - Roles sao imutaveis pos-init; criar test_afere uma unica vez (com
#   OWNER=app_migrator) permite pytest-django reusar/recriar o schema
#   via `--keepdb` ou drop+create-from-template controlado pelo runner
#   sem precisar do privilegio CREATEDB.
# - Procedimento documentado em docs/faseamento/drill-f-b-saida.md #3.
#
# Idempotente: roda apenas na 1a inicializacao do volume (padrao do
# entrypoint oficial do Postgres).

set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Criacao do banco de teste com OWNER=app_migrator.
    -- OWNER eh quem ganha CREATE/CONNECT/TEMPORARY no banco; o runner
    -- de testes (pytest-django) usa DATABASE_MIGRATOR_URL pra DDL, logo
    -- consegue --keepdb (manter) ou drop+recreate apontando aqui.
    SELECT 'CREATE DATABASE test_afere OWNER app_migrator'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'test_afere')
    \gexec

    GRANT CONNECT ON DATABASE test_afere TO app_user, app_migrator;
EOSQL

# Extensoes e default privileges precisam ser aplicadas DENTRO do test_afere
# (extensions sao por-banco; ALTER DEFAULT PRIVILEGES tambem).
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "test_afere" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
    CREATE EXTENSION IF NOT EXISTS citext;
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    CREATE EXTENSION IF NOT EXISTS btree_gist;

    -- No test_afere, app_user tambem tem CREATE no schema public porque
    -- pytest-django chama `migrate` por alias e a tabela django_migrations
    -- precisa existir nos dois alias (default = app_user, migrator =
    -- app_migrator). Em runtime de producao, o banco `afere` mantem
    -- app_user com apenas USAGE — esse grant amplo eh exclusivo do banco
    -- de teste.
    GRANT USAGE, CREATE ON SCHEMA public TO app_user;
    GRANT ALL ON SCHEMA public TO app_migrator;

    ALTER DEFAULT PRIVILEGES FOR ROLE app_migrator IN SCHEMA public
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
    ALTER DEFAULT PRIVILEGES FOR ROLE app_migrator IN SCHEMA public
        GRANT USAGE, SELECT ON SEQUENCES TO app_user;
EOSQL

echo "[init] banco test_afere criado (OWNER=app_migrator) + extensoes + grants."
