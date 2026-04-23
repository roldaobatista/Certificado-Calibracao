CREATE TABLE "public"."nonconformities" (
  "id" UUID NOT NULL,
  "organization_id" UUID NOT NULL,
  "service_order_id" UUID,
  "owner_user_id" UUID,
  "title" VARCHAR(160) NOT NULL,
  "origin_label" VARCHAR(120) NOT NULL,
  "severity_label" VARCHAR(80) NOT NULL,
  "status" VARCHAR(24) NOT NULL,
  "notice_label" VARCHAR(200) NOT NULL,
  "root_cause_label" TEXT NOT NULL,
  "containment_label" TEXT NOT NULL,
  "corrective_action_label" TEXT NOT NULL,
  "evidence_label" TEXT NOT NULL,
  "blockers" TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  "warnings" TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  "opened_at" TIMESTAMPTZ(6) NOT NULL,
  "due_at" TIMESTAMPTZ(6) NOT NULL,
  "resolved_at" TIMESTAMPTZ(6),
  "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT "nonconformities_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "public"."nonconforming_work_cases" (
  "id" UUID NOT NULL,
  "organization_id" UUID NOT NULL,
  "service_order_id" UUID,
  "nonconformity_id" UUID,
  "title" VARCHAR(160) NOT NULL,
  "classification_label" VARCHAR(120) NOT NULL,
  "origin_label" VARCHAR(120) NOT NULL,
  "affected_entity_label" VARCHAR(160) NOT NULL,
  "status" VARCHAR(24) NOT NULL,
  "notice_label" VARCHAR(200) NOT NULL,
  "containment_label" TEXT NOT NULL,
  "release_rule_label" TEXT NOT NULL,
  "evidence_label" TEXT NOT NULL,
  "restoration_label" TEXT NOT NULL,
  "blockers" TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  "warnings" TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT "nonconforming_work_cases_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "public"."internal_audit_cycles" (
  "id" UUID NOT NULL,
  "organization_id" UUID NOT NULL,
  "cycle_label" VARCHAR(120) NOT NULL,
  "window_label" VARCHAR(120) NOT NULL,
  "scope_label" TEXT NOT NULL,
  "auditor_label" VARCHAR(160) NOT NULL,
  "auditee_label" VARCHAR(160) NOT NULL,
  "period_label" VARCHAR(160) NOT NULL,
  "report_label" VARCHAR(200) NOT NULL,
  "evidence_label" TEXT NOT NULL,
  "next_review_label" VARCHAR(200) NOT NULL,
  "notice_label" VARCHAR(200) NOT NULL,
  "status" VARCHAR(24) NOT NULL,
  "checklist_items" JSONB NOT NULL DEFAULT '[]'::jsonb,
  "finding_refs" TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  "blockers" TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  "warnings" TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  "scheduled_at" TIMESTAMPTZ(6) NOT NULL,
  "completed_at" TIMESTAMPTZ(6),
  "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT "internal_audit_cycles_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "public"."management_review_meetings" (
  "id" UUID NOT NULL,
  "organization_id" UUID NOT NULL,
  "title_label" VARCHAR(160) NOT NULL,
  "status" VARCHAR(24) NOT NULL,
  "date_label" VARCHAR(120) NOT NULL,
  "outcome_label" VARCHAR(200) NOT NULL,
  "notice_label" VARCHAR(200) NOT NULL,
  "next_meeting_label" VARCHAR(160) NOT NULL,
  "chair_label" VARCHAR(160) NOT NULL,
  "attendees_label" TEXT NOT NULL,
  "period_label" VARCHAR(160) NOT NULL,
  "ata_label" VARCHAR(200) NOT NULL,
  "evidence_label" TEXT NOT NULL,
  "agenda_items" JSONB NOT NULL DEFAULT '[]'::jsonb,
  "decisions" JSONB NOT NULL DEFAULT '[]'::jsonb,
  "blockers" TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  "warnings" TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  "scheduled_for" TIMESTAMPTZ(6) NOT NULL,
  "held_at" TIMESTAMPTZ(6),
  "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT "management_review_meetings_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "public"."organization_compliance_profiles" (
  "id" UUID NOT NULL,
  "organization_id" UUID NOT NULL,
  "organization_code" VARCHAR(32) NOT NULL,
  "plan_label" VARCHAR(80) NOT NULL,
  "certificate_prefix" VARCHAR(32) NOT NULL,
  "accreditation_number" VARCHAR(80),
  "accreditation_valid_until" DATE,
  "scope_summary" TEXT NOT NULL,
  "cmc_summary" TEXT NOT NULL,
  "scope_item_count" INTEGER NOT NULL DEFAULT 0,
  "cmc_item_count" INTEGER NOT NULL DEFAULT 0,
  "legal_opinion_status" VARCHAR(40) NOT NULL,
  "legal_opinion_reference" VARCHAR(240) NOT NULL,
  "dpa_reference" VARCHAR(240) NOT NULL,
  "normative_governance_status" VARCHAR(40) NOT NULL,
  "normative_governance_owner" VARCHAR(120) NOT NULL,
  "normative_governance_reference" VARCHAR(240) NOT NULL,
  "release_norm_version" VARCHAR(32) NOT NULL,
  "release_norm_status" VARCHAR(40) NOT NULL,
  "last_reviewed_at" TIMESTAMPTZ(6) NOT NULL,
  "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT "organization_compliance_profiles_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "nonconformities_org_title_key" ON "public"."nonconformities"("organization_id", "title");
CREATE INDEX "nonconformities_org_status_due_idx" ON "public"."nonconformities"("organization_id", "status", "due_at");
CREATE INDEX "nonconformities_org_so_idx" ON "public"."nonconformities"("organization_id", "service_order_id");

CREATE UNIQUE INDEX "nonconforming_work_cases_org_title_key" ON "public"."nonconforming_work_cases"("organization_id", "title");
CREATE INDEX "nonconforming_work_cases_org_status_idx" ON "public"."nonconforming_work_cases"("organization_id", "status", "updated_at");
CREATE INDEX "nonconforming_work_cases_org_so_idx" ON "public"."nonconforming_work_cases"("organization_id", "service_order_id");

CREATE UNIQUE INDEX "internal_audit_cycles_org_cycle_key" ON "public"."internal_audit_cycles"("organization_id", "cycle_label");
CREATE INDEX "internal_audit_cycles_org_sched_idx" ON "public"."internal_audit_cycles"("organization_id", "scheduled_at");
CREATE INDEX "internal_audit_cycles_org_status_idx" ON "public"."internal_audit_cycles"("organization_id", "status");

CREATE UNIQUE INDEX "management_review_meetings_org_title_key" ON "public"."management_review_meetings"("organization_id", "title_label");
CREATE INDEX "management_review_meetings_org_sched_idx" ON "public"."management_review_meetings"("organization_id", "scheduled_for");
CREATE INDEX "management_review_meetings_org_status_idx" ON "public"."management_review_meetings"("organization_id", "status");

CREATE UNIQUE INDEX "organization_compliance_profiles_org_key" ON "public"."organization_compliance_profiles"("organization_id");

ALTER TABLE "public"."nonconformities"
  ADD CONSTRAINT "nonconformities_organization_id_fkey"
  FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id")
  ON DELETE RESTRICT;

ALTER TABLE "public"."nonconformities"
  ADD CONSTRAINT "nonconformities_service_order_id_fkey"
  FOREIGN KEY ("service_order_id") REFERENCES "public"."service_orders"("id")
  ON DELETE SET NULL;

ALTER TABLE "public"."nonconformities"
  ADD CONSTRAINT "nonconformities_owner_user_id_fkey"
  FOREIGN KEY ("owner_user_id") REFERENCES "public"."app_users"("id")
  ON DELETE SET NULL;

ALTER TABLE "public"."nonconforming_work_cases"
  ADD CONSTRAINT "nonconforming_work_cases_organization_id_fkey"
  FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id")
  ON DELETE RESTRICT;

ALTER TABLE "public"."nonconforming_work_cases"
  ADD CONSTRAINT "nonconforming_work_cases_service_order_id_fkey"
  FOREIGN KEY ("service_order_id") REFERENCES "public"."service_orders"("id")
  ON DELETE SET NULL;

ALTER TABLE "public"."nonconforming_work_cases"
  ADD CONSTRAINT "nonconforming_work_cases_nonconformity_id_fkey"
  FOREIGN KEY ("nonconformity_id") REFERENCES "public"."nonconformities"("id")
  ON DELETE SET NULL;

ALTER TABLE "public"."internal_audit_cycles"
  ADD CONSTRAINT "internal_audit_cycles_organization_id_fkey"
  FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id")
  ON DELETE RESTRICT;

ALTER TABLE "public"."management_review_meetings"
  ADD CONSTRAINT "management_review_meetings_organization_id_fkey"
  FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id")
  ON DELETE RESTRICT;

ALTER TABLE "public"."organization_compliance_profiles"
  ADD CONSTRAINT "organization_compliance_profiles_organization_id_fkey"
  FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id")
  ON DELETE CASCADE;
