CREATE TABLE IF NOT EXISTS "service_orders" (
  "id" uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "organization_id" uuid NOT NULL REFERENCES "organizations"("id") ON DELETE RESTRICT,
  "customer_id" uuid NOT NULL REFERENCES "customers"("id") ON DELETE RESTRICT,
  "equipment_id" uuid NOT NULL REFERENCES "equipment"("id") ON DELETE RESTRICT,
  "procedure_id" uuid NOT NULL REFERENCES "procedure_revisions"("id") ON DELETE RESTRICT,
  "primary_standard_id" uuid NOT NULL REFERENCES "standards"("id") ON DELETE RESTRICT,
  "executor_user_id" uuid NOT NULL REFERENCES "app_users"("id") ON DELETE RESTRICT,
  "reviewer_user_id" uuid REFERENCES "app_users"("id") ON DELETE SET NULL,
  "work_order_number" varchar(64) NOT NULL,
  "workflow_status" varchar(32) NOT NULL,
  "environment_label" varchar(160) NOT NULL,
  "curve_points_label" varchar(120) NOT NULL,
  "evidence_label" varchar(160) NOT NULL,
  "uncertainty_label" varchar(120) NOT NULL,
  "conformity_label" varchar(160) NOT NULL,
  "comment_draft" text NOT NULL DEFAULT '',
  "created_at" timestamptz(6) NOT NULL DEFAULT now(),
  "accepted_at" timestamptz(6),
  "execution_started_at" timestamptz(6),
  "executed_at" timestamptz(6),
  "review_started_at" timestamptz(6),
  "review_completed_at" timestamptz(6),
  "signature_started_at" timestamptz(6),
  "emitted_at" timestamptz(6),
  "updated_at" timestamptz(6) NOT NULL DEFAULT now(),
  "archived_at" timestamptz(6),
  CONSTRAINT "service_orders_organization_id_work_order_number_key"
    UNIQUE ("organization_id", "work_order_number")
);

CREATE INDEX IF NOT EXISTS "service_orders_organization_id_workflow_status_archived_at_idx"
  ON "service_orders"("organization_id", "workflow_status", "archived_at");
CREATE INDEX IF NOT EXISTS "service_orders_organization_id_customer_id_updated_at_idx"
  ON "service_orders"("organization_id", "customer_id", "updated_at");
CREATE INDEX IF NOT EXISTS "service_orders_organization_id_equipment_id_updated_at_idx"
  ON "service_orders"("organization_id", "equipment_id", "updated_at");

ALTER TABLE "service_orders" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_orders_tenant_isolation"
  ON "service_orders"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);
