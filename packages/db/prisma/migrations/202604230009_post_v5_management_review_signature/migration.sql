ALTER TABLE "public"."management_review_meetings"
  ADD COLUMN IF NOT EXISTS "signed_by_user_id" uuid,
  ADD COLUMN IF NOT EXISTS "signed_by_label" varchar(160),
  ADD COLUMN IF NOT EXISTS "signature_device_id" varchar(120),
  ADD COLUMN IF NOT EXISTS "signature_statement" text,
  ADD COLUMN IF NOT EXISTS "signed_at" timestamptz(6);
