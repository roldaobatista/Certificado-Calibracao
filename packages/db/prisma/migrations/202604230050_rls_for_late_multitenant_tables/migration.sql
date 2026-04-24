ALTER TABLE "public"."certificate_publications" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."nonconformities" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."nonconforming_work_cases" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."internal_audit_cycles" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."management_review_meetings" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."organization_compliance_profiles" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."quality_indicator_snapshots" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "certificate_publications_tenant_isolation"
  ON "public"."certificate_publications"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "nonconformities_tenant_isolation"
  ON "public"."nonconformities"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "nonconforming_work_cases_tenant_isolation"
  ON "public"."nonconforming_work_cases"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "internal_audit_cycles_tenant_isolation"
  ON "public"."internal_audit_cycles"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "management_review_meetings_tenant_isolation"
  ON "public"."management_review_meetings"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "organization_compliance_profiles_tenant_isolation"
  ON "public"."organization_compliance_profiles"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);

CREATE POLICY "quality_indicator_snapshots_tenant_isolation"
  ON "public"."quality_indicator_snapshots"
  FOR ALL
  USING ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid)
  WITH CHECK ("organization_id" = NULLIF(current_setting('app.current_organization_id', true), '')::uuid);
