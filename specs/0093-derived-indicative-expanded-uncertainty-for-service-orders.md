# Spec 0093 - Derived indicative expanded uncertainty for service orders

## Goal

Reduce manual uncertainty entry in the service-order workflow by deriving an indicative expanded uncertainty from the preliminary budget whenever the operator does not provide those fields explicitly.

## Scope

Extend the preliminary-budget engine to expose:

- indicative `Uc`;
- indicative expanded uncertainty `U = k * Uc`;
- indicative `k`, defaulting to `2` when no explicit value is supplied by the service order.

Then use that derived output in service-order persistence as fallback for:

- `uncertaintyLabel`
- `measurementExpandedUncertaintyValue`
- `measurementCoverageFactor`
- `measurementUnit`

## Rules

1. Explicit operator input always wins over derived values.
2. Existing persisted values remain the second priority.
3. Derived values are the third priority and only come from:
   - structured raw capture;
   - frozen metrology snapshots;
   - indicative `k` (`2` by default, or explicit service-order `k` if present).
4. If the preliminary budget is partial, `uncertaintyLabel` may still be derived from the budget summary.
5. If the preliminary budget is blocked, the derived uncertainty fields must not silently fabricate numbers.
6. This wave still does not derive `measurementResultValue`.

## Acceptance criteria

1. Saving a service order without `uncertaintyLabel` succeeds when raw capture plus snapshots allow an indicative budget.
2. The persisted record then exposes:
   - derived `uncertaintyLabel`;
   - derived `measurementExpandedUncertaintyValue`;
   - derived `measurementCoverageFactor`;
   - derived `measurementUnit`.
3. Existing manual values still override any derivation.
4. Dry-run continues to use the stored official fields, but those fields can now be populated by derivation fallback.
