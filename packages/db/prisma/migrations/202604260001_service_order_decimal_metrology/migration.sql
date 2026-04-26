-- Migration: ServiceOrder measurement fields Float -> Decimal(28,12)
-- Auditoria P0-2026-04-26: campos metrológicos oficiais não podem usar Float (IEEE 754)
-- para evitar arredondamento binário e divergência auditável.

ALTER TABLE "service_orders"
  ALTER COLUMN "measurement_result_value" TYPE DECIMAL(28,12),
  ALTER COLUMN "measurement_expanded_uncertainty_value" TYPE DECIMAL(28,12),
  ALTER COLUMN "measurement_coverage_factor" TYPE DECIMAL(28,12);
