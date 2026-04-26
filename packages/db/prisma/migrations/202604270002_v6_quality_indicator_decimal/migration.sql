-- Migration: QualityIndicatorSnapshot Float -> Decimal
-- Owner: metrology-calc + db-schema
-- Data: 2026-04-27

-- Arredondar valores existentes para 6 casas decimais antes de alterar o tipo
UPDATE public.quality_indicator_snapshots
SET value_numeric = ROUND(value_numeric::numeric, 6),
    target_numeric = ROUND(target_numeric::numeric, 6)
WHERE (value_numeric IS NOT NULL OR target_numeric IS NOT NULL)
  AND organization_id IS NOT NULL;

-- Alterar colunas para Decimal(18,6)
ALTER TABLE public.quality_indicator_snapshots
  ALTER COLUMN value_numeric TYPE numeric(18,6) USING ROUND(value_numeric::numeric, 6),
  ALTER COLUMN target_numeric TYPE numeric(18,6) USING ROUND(target_numeric::numeric, 6);
