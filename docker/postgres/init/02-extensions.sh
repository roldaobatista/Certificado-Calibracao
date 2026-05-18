#!/bin/bash
# Habilita extensoes PostgreSQL usadas pelo sistema.
# - pgcrypto: gen_random_uuid() + hash sha256 (audit trail hash chain — ADR-0002 §6)
# - citext:   email case-insensitive
# - pg_trgm:  busca por similaridade (Wave A — modulos com busca textual)

set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
    CREATE EXTENSION IF NOT EXISTS citext;
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
EOSQL

echo "[init] extensoes pgcrypto + citext + pg_trgm habilitadas."
