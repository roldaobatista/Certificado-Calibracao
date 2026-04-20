\echo 'RLS smoke scenario starting'

BEGIN;

DROP SCHEMA IF EXISTS afere_rls_eval CASCADE;
DROP ROLE IF EXISTS afere_rls_eval_app;
DROP ROLE IF EXISTS afere_rls_eval_other;

CREATE ROLE afere_rls_eval_app NOLOGIN;
CREATE ROLE afere_rls_eval_other NOLOGIN;

CREATE SCHEMA afere_rls_eval;

CREATE TABLE afere_rls_eval.certificates (
  id uuid PRIMARY KEY,
  organization_id uuid NOT NULL,
  payload text NOT NULL
);

CREATE TABLE afere_rls_eval.work_orders (
  id uuid PRIMARY KEY,
  organization_id uuid NOT NULL,
  payload text NOT NULL
);

ALTER TABLE afere_rls_eval.certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE afere_rls_eval.work_orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY certificates_tenant_isolation
  ON afere_rls_eval.certificates
  FOR ALL
  USING (organization_id = current_setting('app.organization_id', true)::uuid)
  WITH CHECK (organization_id = current_setting('app.organization_id', true)::uuid);

CREATE POLICY work_orders_tenant_isolation
  ON afere_rls_eval.work_orders
  FOR ALL
  USING (organization_id = current_setting('app.organization_id', true)::uuid)
  WITH CHECK (organization_id = current_setting('app.organization_id', true)::uuid);

GRANT USAGE ON SCHEMA afere_rls_eval TO afere_rls_eval_app;
GRANT SELECT, INSERT ON afere_rls_eval.certificates TO afere_rls_eval_app;
GRANT SELECT, INSERT ON afere_rls_eval.work_orders TO afere_rls_eval_app;

SET SESSION AUTHORIZATION afere_rls_eval_app;

SELECT set_config('app.organization_id', '00000000-0000-0000-0000-00000000000a', true);
INSERT INTO afere_rls_eval.certificates (id, organization_id, payload)
VALUES (
  '10000000-0000-0000-0000-00000000000a',
  '00000000-0000-0000-0000-00000000000a',
  'tenant A certificate'
);
INSERT INTO afere_rls_eval.work_orders (id, organization_id, payload)
VALUES (
  '20000000-0000-0000-0000-00000000000a',
  '00000000-0000-0000-0000-00000000000a',
  'tenant A work order'
);

SELECT set_config('app.organization_id', '00000000-0000-0000-0000-00000000000b', true);
INSERT INTO afere_rls_eval.certificates (id, organization_id, payload)
VALUES (
  '10000000-0000-0000-0000-00000000000b',
  '00000000-0000-0000-0000-00000000000b',
  'tenant B certificate'
);
INSERT INTO afere_rls_eval.work_orders (id, organization_id, payload)
VALUES (
  '20000000-0000-0000-0000-00000000000b',
  '00000000-0000-0000-0000-00000000000b',
  'tenant B work order'
);

SELECT set_config('app.organization_id', '00000000-0000-0000-0000-00000000000a', true);

DO $$
DECLARE
  visible_count integer;
  leaked_count integer;
  cross_join_count integer;
BEGIN
  SELECT count(*) INTO visible_count FROM afere_rls_eval.certificates;
  IF visible_count <> 1 THEN
    RAISE EXCEPTION 'expected tenant A to see 1 certificate, saw %', visible_count;
  END IF;

  SELECT count(*) INTO leaked_count
  FROM afere_rls_eval.certificates
  WHERE organization_id = '00000000-0000-0000-0000-00000000000b';
  IF leaked_count <> 0 THEN
    RAISE EXCEPTION 'tenant A leaked % tenant B certificates', leaked_count;
  END IF;

  SELECT count(*) INTO cross_join_count
  FROM afere_rls_eval.certificates c
  JOIN afere_rls_eval.work_orders w ON c.organization_id <> w.organization_id;
  IF cross_join_count <> 0 THEN
    RAISE EXCEPTION 'cross-tenant join leaked % rows', cross_join_count;
  END IF;

  BEGIN
    INSERT INTO afere_rls_eval.certificates (id, organization_id, payload)
    VALUES (
      '10000000-0000-0000-0000-0000000000ff',
      '00000000-0000-0000-0000-00000000000b',
      'forged tenant B certificate'
    );
    RAISE EXCEPTION 'forged insert unexpectedly succeeded';
  EXCEPTION
    WHEN insufficient_privilege THEN
      NULL;
  END;

  BEGIN
    EXECUTE 'SET ROLE afere_rls_eval_other';
    RAISE EXCEPTION 'SET ROLE escalation unexpectedly succeeded';
  EXCEPTION
    WHEN insufficient_privilege THEN
      NULL;
  END;
END $$;

RESET SESSION AUTHORIZATION;

ROLLBACK;

\echo 'RLS smoke scenario passed'
