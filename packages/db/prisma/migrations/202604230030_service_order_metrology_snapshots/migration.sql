ALTER TABLE "public"."service_orders"
ADD COLUMN IF NOT EXISTS "equipment_metrology_snapshot" jsonb;

ALTER TABLE "public"."service_orders"
ADD COLUMN IF NOT EXISTS "standard_metrology_snapshot" jsonb;
