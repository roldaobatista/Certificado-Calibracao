-- Migration: Adiciona actor_type aos eventos de audit (F-029)
-- Owner: db-schema + backend-api
-- Data: 2026-04-27

ALTER TABLE public.emission_audit_events
  ADD COLUMN IF NOT EXISTS actor_type VARCHAR(16);

ALTER TABLE public.registry_audit_events
  ADD COLUMN IF NOT EXISTS actor_type VARCHAR(16);
