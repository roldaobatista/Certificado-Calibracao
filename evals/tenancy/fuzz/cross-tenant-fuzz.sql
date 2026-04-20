\echo 'RLS fuzz starting'

BEGIN;

DROP SCHEMA IF EXISTS afere_rls_fuzz CASCADE;
DROP ROLE IF EXISTS afere_rls_fuzz_app;

CREATE ROLE afere_rls_fuzz_app NOLOGIN;
CREATE SCHEMA afere_rls_fuzz;

CREATE FUNCTION afere_rls_fuzz.uuid_from_seed(seed text)
RETURNS uuid
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT (
    substr(md5(seed), 1, 8) || '-' ||
    substr(md5(seed), 9, 4) || '-' ||
    substr(md5(seed), 13, 4) || '-' ||
    substr(md5(seed), 17, 4) || '-' ||
    substr(md5(seed), 21, 12)
  )::uuid;
$$;

CREATE TABLE afere_rls_fuzz.certificates (
  id uuid PRIMARY KEY,
  organization_id uuid NOT NULL,
  external_ref text NOT NULL,
  payload jsonb NOT NULL
);

ALTER TABLE afere_rls_fuzz.certificates ENABLE ROW LEVEL SECURITY;

CREATE POLICY certificates_tenant_isolation
  ON afere_rls_fuzz.certificates
  FOR ALL
  USING (organization_id = current_setting('app.organization_id', true)::uuid)
  WITH CHECK (organization_id = current_setting('app.organization_id', true)::uuid);

GRANT USAGE ON SCHEMA afere_rls_fuzz TO afere_rls_fuzz_app;
GRANT EXECUTE ON FUNCTION afere_rls_fuzz.uuid_from_seed(text) TO afere_rls_fuzz_app;
GRANT SELECT, INSERT ON afere_rls_fuzz.certificates TO afere_rls_fuzz_app;

SET SESSION AUTHORIZATION afere_rls_fuzz_app;

SELECT set_config('app.organization_id', '00000000-0000-0000-0000-00000000000b', true);
INSERT INTO afere_rls_fuzz.certificates (id, organization_id, external_ref, payload)
SELECT
  afere_rls_fuzz.uuid_from_seed('tenant-b-seed-' || i::text),
  '00000000-0000-0000-0000-00000000000b',
  'adjacent-' || i::text,
  jsonb_build_object('seed', i, 'tenant', 'b')
FROM generate_series(1, 500) AS i;

SELECT set_config('app.organization_id', '00000000-0000-0000-0000-00000000000a', true);
INSERT INTO afere_rls_fuzz.certificates (id, organization_id, external_ref, payload)
VALUES (
  afere_rls_fuzz.uuid_from_seed('tenant-a-control'),
  '00000000-0000-0000-0000-00000000000a',
  'control-a',
  '{"tenant":"a"}'::jsonb
);

DO $$
DECLARE
  i integer;
  leaked_count integer;
BEGIN
  FOR i IN 1..500 LOOP
    SELECT count(*) INTO leaked_count
    FROM afere_rls_fuzz.certificates
    WHERE id = afere_rls_fuzz.uuid_from_seed('tenant-b-seed-' || i::text)
       OR external_ref = 'adjacent-' || i::text;

    IF leaked_count <> 0 THEN
      RAISE EXCEPTION 'seed % leaked % tenant B rows into tenant A session', i, leaked_count;
    END IF;

    BEGIN
      INSERT INTO afere_rls_fuzz.certificates (id, organization_id, external_ref, payload)
      VALUES (
        afere_rls_fuzz.uuid_from_seed('forged-b-seed-' || i::text),
        '00000000-0000-0000-0000-00000000000b',
        'forged-' || i::text,
        jsonb_build_object('seed', i, 'forged', true)
      );
      RAISE EXCEPTION 'seed % forged insert unexpectedly succeeded', i;
    EXCEPTION
      WHEN insufficient_privilege THEN
        NULL;
    END;
  END LOOP;
END $$;

RESET SESSION AUTHORIZATION;

ROLLBACK;

\echo 'RLS fuzz blocked 500 cross-tenant payloads'
