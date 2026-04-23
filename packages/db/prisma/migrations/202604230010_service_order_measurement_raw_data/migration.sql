ALTER TABLE "public"."service_orders"
  ADD COLUMN IF NOT EXISTS "measurement_raw_data" jsonb;
