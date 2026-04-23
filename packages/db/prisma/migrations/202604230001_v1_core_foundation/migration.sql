CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS "organizations" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "slug" varchar(64) NOT NULL UNIQUE,
  "legal_name" varchar(160) NOT NULL,
  "regulatory_profile" varchar(32) NOT NULL DEFAULT 'type_b',
  "normative_package_version" varchar(80) NOT NULL DEFAULT '2026-04-20-baseline-v0.1.0',
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "app_users" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "organization_id" uuid NOT NULL REFERENCES "organizations"("id") ON DELETE RESTRICT,
  "email" varchar(255) NOT NULL UNIQUE,
  "password_hash" text NOT NULL,
  "display_name" varchar(140) NOT NULL,
  "roles" text[] NOT NULL DEFAULT ARRAY[]::text[],
  "status" varchar(24) NOT NULL DEFAULT 'active',
  "team_name" varchar(120),
  "mfa_enforced" boolean NOT NULL DEFAULT false,
  "mfa_enrolled" boolean NOT NULL DEFAULT false,
  "device_count" integer NOT NULL DEFAULT 0,
  "last_login_at" timestamptz(6),
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS "app_users_organization_id_status_idx"
  ON "app_users"("organization_id", "status");

CREATE TABLE IF NOT EXISTS "user_competencies" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "organization_id" uuid NOT NULL REFERENCES "organizations"("id") ON DELETE RESTRICT,
  "user_id" uuid NOT NULL REFERENCES "app_users"("id") ON DELETE CASCADE,
  "instrument_type" varchar(80) NOT NULL,
  "role_label" varchar(120) NOT NULL,
  "status" varchar(24) NOT NULL,
  "valid_until" date NOT NULL,
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS "user_competencies_organization_id_user_id_idx"
  ON "user_competencies"("organization_id", "user_id");

CREATE TABLE IF NOT EXISTS "app_sessions" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "organization_id" uuid NOT NULL REFERENCES "organizations"("id") ON DELETE RESTRICT,
  "user_id" uuid NOT NULL REFERENCES "app_users"("id") ON DELETE CASCADE,
  "token_hash" text NOT NULL UNIQUE,
  "expires_at" timestamptz(6) NOT NULL,
  "revoked_at" timestamptz(6),
  "created_at" timestamptz(6) NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS "app_sessions_organization_id_user_id_idx"
  ON "app_sessions"("organization_id", "user_id");
CREATE INDEX IF NOT EXISTS "app_sessions_expires_at_idx"
  ON "app_sessions"("expires_at");

CREATE TABLE IF NOT EXISTS "onboarding_states" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "organization_id" uuid NOT NULL UNIQUE REFERENCES "organizations"("id") ON DELETE CASCADE,
  "started_at" timestamptz(6) NOT NULL,
  "completed_at" timestamptz(6),
  "organization_profile_completed" boolean NOT NULL DEFAULT false,
  "primary_signatory_ready" boolean NOT NULL DEFAULT false,
  "certificate_numbering_configured" boolean NOT NULL DEFAULT false,
  "scope_review_completed" boolean NOT NULL DEFAULT false,
  "public_qr_configured" boolean NOT NULL DEFAULT false,
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now()
);

ALTER TABLE "organizations" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "app_users" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "user_competencies" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "app_sessions" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "onboarding_states" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "organizations_tenant_isolation"
  ON "organizations"
  FOR ALL
  USING ("id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "app_users_tenant_isolation"
  ON "app_users"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "user_competencies_tenant_isolation"
  ON "user_competencies"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "app_sessions_tenant_isolation"
  ON "app_sessions"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "onboarding_states_tenant_isolation"
  ON "onboarding_states"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);
