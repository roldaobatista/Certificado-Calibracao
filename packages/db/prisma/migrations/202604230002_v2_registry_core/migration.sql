CREATE TABLE IF NOT EXISTS "customers" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "organization_id" uuid NOT NULL REFERENCES "organizations"("id") ON DELETE RESTRICT,
  "legal_name" varchar(160) NOT NULL,
  "trade_name" varchar(160) NOT NULL,
  "document_label" varchar(80) NOT NULL,
  "segment_label" varchar(120) NOT NULL,
  "account_owner_name" varchar(140) NOT NULL,
  "account_owner_email" varchar(255) NOT NULL,
  "contract_label" text NOT NULL,
  "special_conditions_label" text NOT NULL,
  "contact_name" varchar(140) NOT NULL,
  "contact_role_label" varchar(120) NOT NULL,
  "contact_email" varchar(255) NOT NULL,
  "contact_phone_label" varchar(40),
  "address_line1" varchar(180) NOT NULL,
  "address_city" varchar(80) NOT NULL,
  "address_state" varchar(40) NOT NULL,
  "address_postal_code" varchar(24),
  "address_country" varchar(40) NOT NULL,
  "address_conditions_label" text,
  "archived_at" timestamptz(6),
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS "customers_organization_id_archived_at_idx"
  ON "customers"("organization_id", "archived_at");
CREATE INDEX IF NOT EXISTS "customers_organization_id_trade_name_idx"
  ON "customers"("organization_id", "trade_name");

CREATE TABLE IF NOT EXISTS "standards" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "organization_id" uuid NOT NULL REFERENCES "organizations"("id") ON DELETE RESTRICT,
  "code" varchar(64) NOT NULL,
  "title" varchar(160) NOT NULL,
  "kind_label" varchar(80) NOT NULL,
  "nominal_class_label" varchar(80) NOT NULL,
  "source_label" varchar(80) NOT NULL,
  "certificate_label" varchar(80) NOT NULL,
  "manufacturer_label" varchar(80) NOT NULL,
  "model_label" varchar(80) NOT NULL,
  "serial_number_label" varchar(80) NOT NULL,
  "nominal_value_label" varchar(80) NOT NULL,
  "class_label" varchar(40) NOT NULL,
  "usage_range_label" varchar(120) NOT NULL,
  "measurement_value" numeric(18, 6) NOT NULL,
  "applicable_range_min" numeric(18, 6) NOT NULL,
  "applicable_range_max" numeric(18, 6) NOT NULL,
  "uncertainty_label" varchar(80) NOT NULL,
  "correction_factor_label" varchar(80) NOT NULL,
  "has_valid_certificate" boolean NOT NULL DEFAULT true,
  "certificate_valid_until" date,
  "archived_at" timestamptz(6),
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now(),
  CONSTRAINT "standards_organization_id_code_key" UNIQUE ("organization_id", "code")
);

CREATE INDEX IF NOT EXISTS "standards_organization_id_archived_at_idx"
  ON "standards"("organization_id", "archived_at");

CREATE TABLE IF NOT EXISTS "standard_calibrations" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "organization_id" uuid NOT NULL REFERENCES "organizations"("id") ON DELETE RESTRICT,
  "standard_id" uuid NOT NULL REFERENCES "standards"("id") ON DELETE CASCADE,
  "calibrated_at" date NOT NULL,
  "laboratory_label" varchar(120) NOT NULL,
  "certificate_label" varchar(80) NOT NULL,
  "source_label" varchar(80) NOT NULL,
  "uncertainty_label" varchar(80) NOT NULL,
  "valid_until" date NOT NULL,
  "created_at" timestamptz(6) NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS "standard_calibrations_organization_id_standard_id_calibrated_at_idx"
  ON "standard_calibrations"("organization_id", "standard_id", "calibrated_at");

CREATE TABLE IF NOT EXISTS "procedure_revisions" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "organization_id" uuid NOT NULL REFERENCES "organizations"("id") ON DELETE RESTRICT,
  "code" varchar(64) NOT NULL,
  "title" varchar(160) NOT NULL,
  "type_label" varchar(80) NOT NULL,
  "revision_label" varchar(24) NOT NULL,
  "effective_since" date NOT NULL,
  "effective_until" date,
  "lifecycle_label" varchar(60) NOT NULL,
  "usage_label" varchar(160) NOT NULL,
  "scope_label" text NOT NULL,
  "environment_range_label" varchar(160) NOT NULL,
  "curve_policy_label" text NOT NULL,
  "standards_policy_label" text NOT NULL,
  "approval_label" varchar(160) NOT NULL,
  "related_documents" text[] NOT NULL DEFAULT ARRAY[]::text[],
  "archived_at" timestamptz(6),
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now(),
  CONSTRAINT "procedure_revisions_organization_id_code_revision_label_key"
    UNIQUE ("organization_id", "code", "revision_label")
);

CREATE INDEX IF NOT EXISTS "procedure_revisions_organization_id_code_archived_at_idx"
  ON "procedure_revisions"("organization_id", "code", "archived_at");

CREATE TABLE IF NOT EXISTS "equipment" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "organization_id" uuid NOT NULL REFERENCES "organizations"("id") ON DELETE RESTRICT,
  "customer_id" uuid NOT NULL REFERENCES "customers"("id") ON DELETE RESTRICT,
  "procedure_id" uuid REFERENCES "procedure_revisions"("id") ON DELETE SET NULL,
  "primary_standard_id" uuid REFERENCES "standards"("id") ON DELETE SET NULL,
  "code" varchar(64) NOT NULL,
  "tag_code" varchar(64) NOT NULL,
  "serial_number" varchar(80) NOT NULL,
  "type_model_label" varchar(120) NOT NULL,
  "capacity_class_label" varchar(120) NOT NULL,
  "supporting_standard_codes" text[] NOT NULL DEFAULT ARRAY[]::text[],
  "address_line1" varchar(180) NOT NULL,
  "address_city" varchar(80) NOT NULL,
  "address_state" varchar(40) NOT NULL,
  "address_postal_code" varchar(24),
  "address_country" varchar(40) NOT NULL,
  "address_conditions_label" text,
  "last_calibration_at" date,
  "next_calibration_at" date,
  "archived_at" timestamptz(6),
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now(),
  CONSTRAINT "equipment_organization_id_code_key" UNIQUE ("organization_id", "code")
);

CREATE INDEX IF NOT EXISTS "equipment_organization_id_customer_id_archived_at_idx"
  ON "equipment"("organization_id", "customer_id", "archived_at");
CREATE INDEX IF NOT EXISTS "equipment_organization_id_tag_code_idx"
  ON "equipment"("organization_id", "tag_code");

CREATE TABLE IF NOT EXISTS "registry_audit_events" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "organization_id" uuid NOT NULL REFERENCES "organizations"("id") ON DELETE RESTRICT,
  "entity_type" varchar(40) NOT NULL,
  "entity_id" uuid NOT NULL,
  "action" varchar(40) NOT NULL,
  "actor_user_id" uuid REFERENCES "app_users"("id") ON DELETE SET NULL,
  "summary" varchar(240) NOT NULL,
  "created_at" timestamptz(6) NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS "registry_audit_events_organization_id_entity_type_entity_id_created_at_idx"
  ON "registry_audit_events"("organization_id", "entity_type", "entity_id", "created_at");

ALTER TABLE "customers" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "standards" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "standard_calibrations" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "procedure_revisions" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "equipment" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "registry_audit_events" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "customers_tenant_isolation"
  ON "customers"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "standards_tenant_isolation"
  ON "standards"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "standard_calibrations_tenant_isolation"
  ON "standard_calibrations"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "procedure_revisions_tenant_isolation"
  ON "procedure_revisions"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "equipment_tenant_isolation"
  ON "equipment"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "registry_audit_events_tenant_isolation"
  ON "registry_audit_events"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);
