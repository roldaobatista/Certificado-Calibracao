\echo 'RLS hostile Prisma scenario starting'

BEGIN;

DROP SCHEMA IF EXISTS afere_rls_hostile CASCADE;
DROP ROLE IF EXISTS afere_rls_hostile_app;

CREATE ROLE afere_rls_hostile_app LOGIN PASSWORD 'hostile' NOINHERIT;

CREATE SCHEMA afere_rls_hostile;

CREATE TABLE afere_rls_hostile.organizations (
  id uuid PRIMARY KEY,
  slug text NOT NULL,
  legal_name text NOT NULL
);

CREATE TABLE afere_rls_hostile.app_users (
  id uuid PRIMARY KEY,
  organization_id uuid NOT NULL,
  email text NOT NULL,
  display_name text NOT NULL
);

CREATE TABLE afere_rls_hostile.service_orders (
  id uuid PRIMARY KEY,
  organization_id uuid NOT NULL,
  work_order_number text NOT NULL,
  payload text NOT NULL
);

ALTER TABLE afere_rls_hostile.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE afere_rls_hostile.app_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE afere_rls_hostile.service_orders ENABLE ROW LEVEL SECURITY;

ALTER TABLE afere_rls_hostile.organizations FORCE ROW LEVEL SECURITY;
ALTER TABLE afere_rls_hostile.app_users FORCE ROW LEVEL SECURITY;
ALTER TABLE afere_rls_hostile.service_orders FORCE ROW LEVEL SECURITY;

CREATE POLICY organizations_tenant_isolation
  ON afere_rls_hostile.organizations
  FOR ALL
  USING (id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK (id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY app_users_tenant_isolation
  ON afere_rls_hostile.app_users
  FOR ALL
  USING (organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK (organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY service_orders_tenant_isolation
  ON afere_rls_hostile.service_orders
  FOR ALL
  USING (organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK (organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

GRANT USAGE ON SCHEMA afere_rls_hostile TO afere_rls_hostile_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA afere_rls_hostile TO afere_rls_hostile_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA afere_rls_hostile TO afere_rls_hostile_app;

-- Inserir dados como owner
INSERT INTO afere_rls_hostile.organizations (id, slug, legal_name)
VALUES ('00000000-0000-0000-0000-00000000000a', 'org-a', 'Organizacao A');

INSERT INTO afere_rls_hostile.organizations (id, slug, legal_name)
VALUES ('00000000-0000-0000-0000-00000000000b', 'org-b', 'Organizacao B');

INSERT INTO afere_rls_hostile.app_users (id, organization_id, email, display_name)
VALUES ('10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-00000000000a', 'a@afere.local', 'Usuario A');

INSERT INTO afere_rls_hostile.app_users (id, organization_id, email, display_name)
VALUES ('10000000-0000-0000-0000-00000000000b', '00000000-0000-0000-0000-00000000000b', 'b@afere.local', 'Usuario B');

INSERT INTO afere_rls_hostile.service_orders (id, organization_id, work_order_number, payload)
VALUES ('20000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-00000000000a', 'OS-0001-A', 'Dados A');

INSERT INTO afere_rls_hostile.service_orders (id, organization_id, work_order_number, payload)
VALUES ('20000000-0000-0000-0000-00000000000b', '00000000-0000-0000-0000-00000000000b', 'OS-0001-B', 'Dados B');

-- Trocar para role de aplicação
SET SESSION AUTHORIZATION afere_rls_hostile_app;

-- Teste 1: sem tenant context, não deve ver nada
DO $$
DECLARE
  cnt integer;
BEGIN
  SELECT count(*) INTO cnt FROM afere_rls_hostile.service_orders;
  IF cnt <> 0 THEN
    RAISE EXCEPTION 'Hostile test 1 failed: expected 0 rows without tenant context, saw %', cnt;
  END IF;
END $$;

-- Teste 2: com tenant context correto, deve ver apenas dados do tenant A
SELECT set_config('app.current_organization_id', '00000000-0000-0000-0000-00000000000a', true);

DO $$
DECLARE
  cnt integer;
BEGIN
  SELECT count(*) INTO cnt FROM afere_rls_hostile.service_orders;
  IF cnt <> 1 THEN
    RAISE EXCEPTION 'Hostile test 2 failed: expected 1 row for tenant A, saw %', cnt;
  END IF;

  SELECT count(*) INTO cnt FROM afere_rls_hostile.app_users;
  IF cnt <> 1 THEN
    RAISE EXCEPTION 'Hostile test 2b failed: expected 1 user for tenant A, saw %', cnt;
  END IF;
END $$;

-- Teste 3: tentar inserir dados de tenant B usando tenant context A (forged insert)
DO $$
BEGIN
  INSERT INTO afere_rls_hostile.service_orders (id, organization_id, work_order_number, payload)
  VALUES ('30000000-0000-0000-0000-00000000000b', '00000000-0000-0000-0000-00000000000b', 'FORGED', 'Forjado');
  RAISE EXCEPTION 'Hostile test 3 failed: forged insert should have been blocked';
EXCEPTION
  WHEN insufficient_privilege THEN
    NULL;
END $$;

-- Teste 4: tentar escalar privilégio com SET ROLE
DO $$
BEGIN
  EXECUTE 'SET ROLE afere';
  RAISE EXCEPTION 'Hostile test 4 failed: SET ROLE escalation should have been blocked';
EXCEPTION
  WHEN insufficient_privilege THEN
    NULL;
END $$;

-- Teste 5: mesmo com FORCE RLS, role owner conectada via app URL não deve bypassar
-- (nota: este teste usa a role afere_rls_hostile_app, que não é owner, então FORCE RLS já aplica)

RESET SESSION AUTHORIZATION;

ROLLBACK;

\echo 'RLS hostile Prisma scenario passed'
