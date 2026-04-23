ALTER TABLE "service_orders"
  ADD COLUMN IF NOT EXISTS "signatory_user_id" uuid REFERENCES "app_users"("id") ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS "measurement_result_value" double precision,
  ADD COLUMN IF NOT EXISTS "measurement_expanded_uncertainty_value" double precision,
  ADD COLUMN IF NOT EXISTS "measurement_coverage_factor" double precision,
  ADD COLUMN IF NOT EXISTS "measurement_unit" varchar(24),
  ADD COLUMN IF NOT EXISTS "decision_rule_label" varchar(160),
  ADD COLUMN IF NOT EXISTS "decision_outcome_label" varchar(160),
  ADD COLUMN IF NOT EXISTS "free_text_statement" text,
  ADD COLUMN IF NOT EXISTS "review_decision" varchar(24) NOT NULL DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS "review_decision_comment" text NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS "review_device_id" varchar(120),
  ADD COLUMN IF NOT EXISTS "signature_device_id" varchar(120),
  ADD COLUMN IF NOT EXISTS "signature_statement" text,
  ADD COLUMN IF NOT EXISTS "certificate_number" varchar(64),
  ADD COLUMN IF NOT EXISTS "certificate_revision" varchar(16),
  ADD COLUMN IF NOT EXISTS "public_verification_token" varchar(80),
  ADD COLUMN IF NOT EXISTS "document_hash" varchar(128),
  ADD COLUMN IF NOT EXISTS "qr_host" varchar(160),
  ADD COLUMN IF NOT EXISTS "signed_at" timestamptz(6);

CREATE UNIQUE INDEX IF NOT EXISTS "service_orders_organization_id_certificate_number_key"
  ON "service_orders"("organization_id", "certificate_number");

CREATE TABLE IF NOT EXISTS "emission_audit_events" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "organization_id" uuid NOT NULL REFERENCES "organizations"("id") ON DELETE RESTRICT,
  "service_order_id" uuid NOT NULL REFERENCES "service_orders"("id") ON DELETE CASCADE,
  "actor_user_id" uuid REFERENCES "app_users"("id") ON DELETE SET NULL,
  "action" varchar(64) NOT NULL,
  "actor_label" varchar(160) NOT NULL,
  "entity_label" varchar(160) NOT NULL,
  "device_id" varchar(120),
  "certificate_number" varchar(64),
  "prev_hash" varchar(64) NOT NULL,
  "hash" varchar(64) NOT NULL,
  "occurred_at" timestamptz(6) NOT NULL,
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  CONSTRAINT "emission_audit_events_service_order_id_hash_key"
    UNIQUE ("service_order_id", "hash")
);

CREATE INDEX IF NOT EXISTS "emission_audit_events_organization_id_service_order_id_occurred_at_idx"
  ON "emission_audit_events"("organization_id", "service_order_id", "occurred_at");
CREATE INDEX IF NOT EXISTS "emission_audit_events_organization_id_action_occurred_at_idx"
  ON "emission_audit_events"("organization_id", "action", "occurred_at");

ALTER TABLE "emission_audit_events" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "emission_audit_events_tenant_isolation"
  ON "emission_audit_events"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);
