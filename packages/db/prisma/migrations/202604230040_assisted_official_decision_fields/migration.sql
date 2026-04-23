ALTER TABLE "public"."service_orders"
ADD COLUMN "indicative_decision_snapshot" JSONB,
ADD COLUMN "official_decision_diverges_from_indicative" BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN "official_decision_justification" TEXT;
