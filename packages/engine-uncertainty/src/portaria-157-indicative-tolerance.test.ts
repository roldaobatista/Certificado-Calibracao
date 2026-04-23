import assert from "node:assert/strict";
import { test } from "node:test";

import { evaluatePortaria157IndicativeTolerance } from "./portaria-157-indicative-tolerance.js";
import { analyzeRawMeasurementData } from "./raw-measurement-analysis.js";

test("evaluates linearity points against the indicative EMA bands from Portaria 157", () => {
  const rawAnalysis = analyzeRawMeasurementData({
    captureMode: "manual",
    repeatabilityRuns: [
      {
        loadValue: 15,
        unit: "kg",
        indications: [15, 15.001, 15],
      },
    ],
    eccentricityPoints: [
      {
        positionLabel: "centro",
        loadValue: 15,
        indicationValue: 15,
        unit: "kg",
      },
      {
        positionLabel: "frontal",
        loadValue: 15,
        indicationValue: 15.001,
        unit: "kg",
      },
    ],
    linearityPoints: [
      {
        pointLabel: "50%",
        appliedLoadValue: 15,
        referenceValue: 15,
        indicationValue: 15.001,
        unit: "kg",
      },
      {
        pointLabel: "100%",
        appliedLoadValue: 300,
        referenceValue: 300,
        indicationValue: 300.08,
        unit: "kg",
      },
    ],
    evidenceAttachments: [
      {
        attachmentId: "evidence-001",
        label: "Foto do ensaio",
        kind: "photo",
        mediaType: "image/jpeg",
      },
    ],
  });

  const evaluation = evaluatePortaria157IndicativeTolerance(rawAnalysis, {
    normativeClass: "iii",
    verificationScaleIntervalValue: 0.05,
    maximumCapacityValue: 300,
    expectedMeasurementUnit: "kg",
  });

  assert.equal(evaluation.readyForIndicativeUse, true);
  assert.equal(evaluation.evaluatedPointCount, 2);
  assert.equal(evaluation.failingPointCount, 0);
  assert.equal(evaluation.points[0]?.emaMultiplier, 1);
  assert.equal(evaluation.points[0]?.withinTolerance, true);
  assert.equal(evaluation.points[1]?.emaMultiplier, 3);
  assert.equal(Number((evaluation.points[1]?.toleranceValue ?? 0).toFixed(6)), 0.15);
  assert.equal(evaluation.points[1]?.withinTolerance, true);
  assert.match(evaluation.summaryLabel, /Todos os pontos dentro do EMA/i);
});

test("fails closed when a linearity point exceeds the indicative EMA", () => {
  const rawAnalysis = analyzeRawMeasurementData({
    captureMode: "manual",
    repeatabilityRuns: [
      {
        loadValue: 15,
        unit: "kg",
        indications: [15, 15.001],
      },
    ],
    eccentricityPoints: [
      {
        positionLabel: "centro",
        loadValue: 15,
        indicationValue: 15,
        unit: "kg",
      },
      {
        positionLabel: "frontal",
        loadValue: 15,
        indicationValue: 15.001,
        unit: "kg",
      },
    ],
    linearityPoints: [
      {
        pointLabel: "100%",
        appliedLoadValue: 300,
        referenceValue: 300,
        indicationValue: 300.3,
        unit: "kg",
      },
    ],
    evidenceAttachments: [
      {
        attachmentId: "evidence-001",
        label: "Foto do ensaio",
        kind: "photo",
        mediaType: "image/jpeg",
      },
    ],
  });

  const evaluation = evaluatePortaria157IndicativeTolerance(rawAnalysis, {
    normativeClass: "iii",
    verificationScaleIntervalValue: 0.05,
    expectedMeasurementUnit: "kg",
  });

  assert.equal(evaluation.failingPointCount, 1);
  assert.match(evaluation.blockers.join(" "), /fora do EMA indicativo/i);
  assert.match(evaluation.summaryLabel, /bloqueado/i);
});

test("keeps the EMA evaluation partial when class or e are missing", () => {
  const rawAnalysis = analyzeRawMeasurementData({
    captureMode: "manual",
    repeatabilityRuns: [],
    eccentricityPoints: [],
    linearityPoints: [
      {
        pointLabel: "50%",
        appliedLoadValue: 15,
        referenceValue: 15,
        indicationValue: 15.001,
        unit: "kg",
      },
    ],
    evidenceAttachments: [],
  });

  const evaluation = evaluatePortaria157IndicativeTolerance(rawAnalysis, {
    expectedMeasurementUnit: "kg",
  });

  assert.equal(evaluation.readyForIndicativeUse, false);
  assert.equal(evaluation.evaluatedPointCount, 0);
  assert.match(evaluation.summaryLabel, /parcial/i);
  assert.match(evaluation.warnings.join(" "), /classe normativa/i);
  assert.match(evaluation.warnings.join(" "), /sem e/i);
});

test("propagates blocked raw analysis into the indicative EMA evaluation", () => {
  const rawAnalysis = analyzeRawMeasurementData(
    {
      captureMode: "manual",
      repeatabilityRuns: [
        {
          loadValue: 1,
          unit: "g",
          indications: [1, 1.001],
        },
      ],
      eccentricityPoints: [],
      linearityPoints: [
        {
          pointLabel: "50%",
          appliedLoadValue: 1,
          referenceValue: 1,
          indicationValue: 1.001,
          unit: "g",
        },
      ],
      evidenceAttachments: [],
    },
    {
      expectedMeasurementUnit: "kg",
    },
  );

  const evaluation = evaluatePortaria157IndicativeTolerance(rawAnalysis, {
    normativeClass: "iii",
    verificationScaleIntervalValue: 0.001,
    expectedMeasurementUnit: "kg",
  });

  assert.equal(evaluation.readyForIndicativeUse, false);
  assert.match(evaluation.blockers.join(" "), /unidade esperada/i);
});
