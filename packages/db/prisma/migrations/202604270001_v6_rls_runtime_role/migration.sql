-- Migration: RLS runtime role + FORCE RLS
-- Owner: db-schema
-- Data: 2026-04-27
--
-- Objetivo:
--   1. Criar role afere_app (não-owner, sem bypass RLS).
--   2. Conceder grants mínimos para operações CRUD em todas as tabelas multitenant.
--   3. Aplicar FORCE ROW LEVEL SECURITY em todas as tabelas com policies de tenant isolation.
--   4. Garantir que afere_app NÃO seja dono de nenhum objeto.

-- 1. Criar role de aplicação (idempotente)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'afere_app') THEN
    CREATE ROLE afere_app NOLOGIN;
  END IF;
END
$$;

-- 2. Revogar privilégios padrão para garantir base limpa
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM afere_app;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM afere_app;
REVOKE ALL ON SCHEMA public FROM afere_app;

-- 3. Conceder uso do schema e sequências
GRANT USAGE ON SCHEMA public TO afere_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO afere_app;

-- 4. Conceder CRUD mínimo em todas as tabelas do schema public
--    (exclui tabelas de sistema e tabelas internas do Prisma)
DO $$
DECLARE
  tbl RECORD;
BEGIN
  FOR tbl IN
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = 'public'
      AND tablename NOT LIKE 'pg_%'
      AND tablename NOT LIKE '_prisma%'
  LOOP
    EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON public.%I TO afere_app', tbl.tablename);
  END LOOP;
END
$$;

-- 5. Aplicar FORCE ROW LEVEL SECURITY em todas as tabelas com RLS habilitado
DO $$
DECLARE
  tbl RECORD;
BEGIN
  FOR tbl IN
    SELECT relname AS tablename
    FROM pg_class
    JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
    WHERE pg_namespace.nspname = 'public'
      AND pg_class.relrowsecurity = true
      AND pg_class.relforcerowsecurity = false
  LOOP
    EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY', tbl.tablename);
  END LOOP;
END
$$;
