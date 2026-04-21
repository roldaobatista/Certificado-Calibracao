import assert from "node:assert/strict";
import { test } from "node:test";

import { buildCertificateMeasurementDeclaration } from "./measurement-declarations.js";

test("builds a structured declaration with result, expanded uncertainty and coverage factor", () => {
  const declaration = buildCertificateMeasurementDeclaration({
    resultValue: 10.12,
    expandedUncertaintyValue: 0.15,
    coverageFactor: 2,
    unit: "g",
  });

  assert.deepEqual(declaration.result, {
    value: 10.12,
    unit: "g",
    formatted: "10.12 g",
  });
  assert.deepEqual(declaration.expandedUncertainty, {
    value: 0.15,
    unit: "g",
    formatted: "±0.15 g",
  });
  assert.deepEqual(declaration.coverageFactor, {
    value: 2,
    formatted: "k=2",
  });
  assert.equal(
    declaration.summary,
    "Resultado: 10.12 g | U: ±0.15 g | k=2",
  );
});

test("fails closed when any mandatory declaration field is missing", () => {
  assert.throws(
    () =>
      buildCertificateMeasurementDeclaration({
        resultValue: 10.12,
        expandedUncertaintyValue: 0.15,
        coverageFactor: 2,
        unit: "",
      }),
    /missing_unit/,
  );
});

test("fails closed when result, uncertainty or k are non-finite or invalid", () => {
  assert.throws(
    () =>
      buildCertificateMeasurementDeclaration({
        resultValue: Number.NaN,
        expandedUncertaintyValue: 0.15,
        coverageFactor: 2,
        unit: "g",
      }),
    /invalid_result_value/,
  );

  assert.throws(
    () =>
      buildCertificateMeasurementDeclaration({
        resultValue: 10.12,
        expandedUncertaintyValue: -0.15,
        coverageFactor: 2,
        unit: "g",
      }),
    /invalid_expanded_uncertainty_value/,
  );

  assert.throws(
    () =>
      buildCertificateMeasurementDeclaration({
        resultValue: 10.12,
        expandedUncertaintyValue: 0.15,
        coverageFactor: 0,
        unit: "g",
      }),
    /invalid_coverage_factor/,
  );
});
