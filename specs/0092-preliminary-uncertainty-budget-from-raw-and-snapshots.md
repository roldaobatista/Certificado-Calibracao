# Spec 0092 - Preliminary uncertainty budget from raw capture and metrology snapshots

## Goal

Add an intermediate metrology layer that derives a bounded preliminary uncertainty budget from:

- structured raw capture already persisted on the service order;
- frozen metrology snapshots of the equipment and the primary standard.

This layer is informational and review-oriented. It must not replace the official certificate declaration yet.

## Scope

Implement a new helper in `packages/engine-uncertainty` that:

1. consumes the normalized raw analysis already produced from structured capture;
2. derives the following preliminary components when possible:
   - `u_d0 = d / sqrt(12)`
   - `u_dL = d / sqrt(12)`
   - `u_rep` from the worst repeatability series, applying a floor tied to `0.41 * d`
   - `u_mc = U / k` from the primary standard snapshot
3. combines the available components in quadrature only when the budget is complete;
4. fails closed on inconsistent raw data and stays partial when snapshots are incomplete.

## Inputs

### Raw side

- `RawMeasurementAnalysis`
- worst repeatability standard deviation (`smax`)
- raw unit already normalized by the raw-analysis layer

### Snapshot side

- equipment `readabilityValue`
- equipment or standard measurement unit
- standard `expandedUncertaintyValue`
- standard `coverageFactorK`

## Rules

1. The helper must reuse the raw-analysis result. It must not re-parse raw JSON.
2. If the raw-analysis layer is already blocked, the preliminary budget is blocked as well.
3. If `readabilityValue` is available:
   - resolution components are mandatory for a complete budget;
   - repeatability must use `max(smax, 0.41 * d)`.
4. If standard `U` and `k` are available:
   - derive `u_mc = U / k`;
   - if only one of them is available, keep the budget partial and warn.
5. The combined standard uncertainty is only exposed when the four components above are present and valid.
6. The dry-run and official measurement declaration remain unchanged in this wave.

## Integration

Expose the preliminary budget in:

- persisted service-order review metrics/checklist;
- persisted certificate preview sections.

Do not persist this budget yet. It is derived at read time from canonical snapshots plus raw capture.

## Acceptance criteria

1. A service order with structured raw capture plus complete metrology snapshots shows:
   - component labels;
   - a combined preliminary `Uc`;
   - whether the repeatability floor was applied.
2. Missing `d` or missing standard `U/k` does not crash the flow. It yields a partial budget.
3. Mixed-unit or blocked raw capture yields a blocked preliminary budget.
4. Engine unit tests cover:
   - complete budget with repeatability floor;
   - partial budget when snapshots are incomplete;
   - blocked budget when raw analysis is already incoherent.
