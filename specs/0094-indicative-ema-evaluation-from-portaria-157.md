# Spec 0094 - Indicative EMA evaluation from Portaria Inmetro 157/2022

## Goal

Add an indicative legal-tolerance evaluation for NAWI/IPNA service orders using:

- frozen equipment metrology snapshots;
- structured linearity points already normalized in the raw-analysis layer.

## Scope

Implement a new helper in `packages/engine-uncertainty` that:

1. reuses `RawMeasurementAnalysis`;
2. reads equipment context (`classe`, `e`, `Max`, unidade);
3. evaluates each linearity point against the EMA bands from Portaria Inmetro 157/2022;
4. returns a per-point result plus an overall summary.

## Rules

1. This helper is indicative and review-oriented in this wave.
2. It must not replace the official decision rule yet.
3. If raw analysis is already blocked, the EMA evaluation is blocked too.
4. If `normativeClass` or `verificationScaleIntervalValue` are missing, the evaluation becomes partial and warns.
5. The applicable EMA multiplier is:
   - classe I: `1e` to `50_000e`, `2e` to `200_000e`, otherwise `3e`
   - classe II: `1e` to `5_000e`, `2e` to `20_000e`, otherwise `3e`
   - classe III: `1e` to `500e`, `2e` to `2_000e`, otherwise `3e`
   - classe IIII: `1e` to `50e`, `2e` to `200e`, otherwise `3e`
6. Per-point verdict is based on `abs(errorValue) <= multiplier * e`.

## Integration

Expose the indicative EMA evaluation in:

- persisted service-order review checklist and metrics;
- persisted certificate preview section.

## Acceptance criteria

1. A service order with class/e snapshot plus linearity points shows an indicative EMA summary.
2. A point outside tolerance marks the EMA evaluation as failed in review.
3. Missing class/e does not crash the flow and yields a partial evaluation.
4. Mixed-unit or blocked raw capture yields blocked EMA evaluation.
