# Spec 0095 - Indicative decision rule from preliminary uncertainty and EMA

## Goal

Add an indicative decision evaluation for service orders by combining:

- the preliminary expanded uncertainty already derived from raw capture and snapshots;
- the indicative EMA evaluation based on Portaria Inmetro 157/2022;
- the configured decision-rule label of the service order.

## Scope

Implement a review-oriented helper in `packages/engine-uncertainty` that:

1. resolves a decision mode from the service-order decision-rule label;
2. evaluates each point of linearity against tolerance, optionally considering a guard band;
3. returns an overall indicative verdict and a summary.

## Modes

- `simple_tolerance`
  - activated by labels such as `ILAC G8 sem banda de guarda`;
  - verdict per point: `abs(error) <= EMA`.
- `guard_band`
  - activated by labels such as `ILAC G8 com banda de guarda`;
  - uses the preliminary expanded uncertainty `U`;
  - conforming if `abs(error) + U <= EMA`;
  - non-conforming if `abs(error) - U > EMA`;
  - otherwise inconclusive.

## Non-goals in this wave

- do not overwrite `decisionOutcomeLabel`;
- do not block signature queue automatically;
- do not replace the official decision workflow yet.

## Integration

Expose the indicative decision only in:

- persisted service-order review metrics;
- persisted certificate preview decision section.

## Acceptance criteria

1. A service order with rule label, preliminary `U`, and EMA indicative data shows an indicative decision summary.
2. Guard-band mode can return `inconclusiva` when the current derived `U` does not support a crisp verdict.
3. Missing rule label or missing `U` does not crash the flow and yields a partial summary.
4. Existing service-order scenarios remain stable because this wave is informational, not gating.
