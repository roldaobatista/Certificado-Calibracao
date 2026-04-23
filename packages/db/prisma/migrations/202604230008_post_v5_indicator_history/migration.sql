CREATE TABLE "public"."quality_indicator_snapshots" (
  "id" UUID NOT NULL,
  "organization_id" UUID NOT NULL,
  "indicator_id" VARCHAR(80) NOT NULL,
  "month_start" DATE NOT NULL,
  "value_numeric" DOUBLE PRECISION NOT NULL,
  "target_numeric" DOUBLE PRECISION,
  "status" VARCHAR(24) NOT NULL,
  "source_label" VARCHAR(160) NOT NULL,
  "evidence_label" TEXT NOT NULL,
  "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT "quality_indicator_snapshots_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "quality_indicator_snapshots_org_indicator_month_key"
  ON "public"."quality_indicator_snapshots"("organization_id", "indicator_id", "month_start");

CREATE INDEX "quality_indicator_snapshots_org_month_idx"
  ON "public"."quality_indicator_snapshots"("organization_id", "month_start");

CREATE INDEX "quality_indicator_snapshots_org_indicator_month_idx"
  ON "public"."quality_indicator_snapshots"("organization_id", "indicator_id", "month_start");

ALTER TABLE "public"."quality_indicator_snapshots"
  ADD CONSTRAINT "quality_indicator_snapshots_organization_id_fkey"
  FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id")
  ON DELETE RESTRICT;
