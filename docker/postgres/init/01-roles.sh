#!/bin/bash
# Cria as 2 roles do app conforme ADR-0002 §2.
# Roda automaticamente na 1a inicializacao do container postgres.
#
# app_user      = role de runtime (Django app + workers Procrastinate)
#                 NOBYPASSRLS + NOSUPERUSER → defesa em profundidade contra
#                 vazamento cross-tenant (INV-TENANT-004).
# app_migrator  = role separada APENAS para migrations (DDL).
#                 Separacao previne agente escrever migration que altera dados
#                 de producao sem perceber.

set -euo pipefail

: "${APP_USER_PASSWORD:?APP_USER_PASSWORD nao definido}"
: "${APP_MIGRATOR_PASSWORD:?APP_MIGRATOR_PASSWORD nao definido}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- =============================================================
    -- Role app_user (acesso normal do app — sem bypass de RLS)
    -- =============================================================
    CREATE ROLE app_user WITH
        LOGIN
        PASSWORD '${APP_USER_PASSWORD}'
        NOSUPERUSER
        NOBYPASSRLS
        NOCREATEDB
        NOCREATEROLE
        NOREPLICATION;

    -- =============================================================
    -- Role app_migrator (DDL apenas — tambem sem bypass)
    -- =============================================================
    CREATE ROLE app_migrator WITH
        LOGIN
        PASSWORD '${APP_MIGRATOR_PASSWORD}'
        NOSUPERUSER
        NOBYPASSRLS
        NOCREATEDB
        NOCREATEROLE
        NOREPLICATION;

    -- =============================================================
    -- Grants
    -- =============================================================
    GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO app_user, app_migrator;
    GRANT USAGE ON SCHEMA public TO app_user;

    -- app_migrator: pode criar/alterar schema; default privileges
    -- garantem que tabelas novas (criadas em migrations) ja saem com
    -- SELECT/INSERT/UPDATE/DELETE pra app_user.
    GRANT ALL ON SCHEMA public TO app_migrator;
    ALTER DEFAULT PRIVILEGES FOR ROLE app_migrator IN SCHEMA public
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
    ALTER DEFAULT PRIVILEGES FOR ROLE app_migrator IN SCHEMA public
        GRANT USAGE, SELECT ON SEQUENCES TO app_user;
EOSQL

echo "[init] roles app_user e app_migrator criadas (NOBYPASSRLS)."
