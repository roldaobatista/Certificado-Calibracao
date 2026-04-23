ALTER TABLE "public"."standards"
ADD COLUMN IF NOT EXISTS "metrology_profile" jsonb;

ALTER TABLE "public"."equipment"
ADD COLUMN IF NOT EXISTS "metrology_profile" jsonb;
