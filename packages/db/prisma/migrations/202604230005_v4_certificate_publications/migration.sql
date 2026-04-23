CREATE TABLE IF NOT EXISTS "public"."certificate_publications" (
  "id" uuid NOT NULL,
  "organization_id" uuid NOT NULL,
  "service_order_id" uuid NOT NULL,
  "certificate_number" varchar(64) NOT NULL,
  "revision" varchar(16) NOT NULL,
  "public_verification_token" varchar(80) NOT NULL,
  "document_hash" varchar(128) NOT NULL,
  "qr_host" varchar(160) NOT NULL,
  "signed_at" timestamptz(6),
  "issued_at" timestamptz(6) NOT NULL,
  "superseded_at" timestamptz(6),
  "replacement_publication_id" uuid,
  "previous_certificate_hash" varchar(128),
  "notification_recipient" varchar(255),
  "notification_sent_at" timestamptz(6),
  "reissue_reason" varchar(160),
  "created_at" timestamptz(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" timestamptz(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "certificate_publications_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "certificate_publications_public_verification_token_key"
  ON "public"."certificate_publications"("public_verification_token");

CREATE UNIQUE INDEX IF NOT EXISTS "certificate_publications_replacement_publication_id_key"
  ON "public"."certificate_publications"("replacement_publication_id");

CREATE UNIQUE INDEX IF NOT EXISTS "certificate_publications_organization_id_certificate_number_revision_key"
  ON "public"."certificate_publications"("organization_id", "certificate_number", "revision");

CREATE INDEX IF NOT EXISTS "certificate_publications_organization_id_service_order_id_issued_at_idx"
  ON "public"."certificate_publications"("organization_id", "service_order_id", "issued_at");

CREATE INDEX IF NOT EXISTS "certificate_publications_organization_id_issued_at_idx"
  ON "public"."certificate_publications"("organization_id", "issued_at");

ALTER TABLE "public"."certificate_publications"
  ADD CONSTRAINT "certificate_publications_organization_id_fkey"
  FOREIGN KEY ("organization_id") REFERENCES "public"."organizations"("id")
  ON DELETE RESTRICT;

ALTER TABLE "public"."certificate_publications"
  ADD CONSTRAINT "certificate_publications_service_order_id_fkey"
  FOREIGN KEY ("service_order_id") REFERENCES "public"."service_orders"("id")
  ON DELETE CASCADE;

ALTER TABLE "public"."certificate_publications"
  ADD CONSTRAINT "certificate_publications_replacement_publication_id_fkey"
  FOREIGN KEY ("replacement_publication_id") REFERENCES "public"."certificate_publications"("id")
  ON DELETE SET NULL;
