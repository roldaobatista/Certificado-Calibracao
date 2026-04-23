import assert from "node:assert/strict";
import { test } from "node:test";

import { analyzeRawMeasurementData } from "./raw-measurement-analysis.js";

test("analyzes repeatability, eccentricity and linearity from structured raw data", () => {
  const analysis = analyzeRawMeasurementData({
    captureMode: "manual",
    environment: {
      temperatureStartC: 22.1,
      temperatureEndC: 22.3,
      relativeHumidityPercent: 48,
      atmosphericPressureHpa: 1013,
    },
    repeatabilityRuns: [
      {
        loadValue: 15,
        unit: "kg",
        indications: [15, 15.001, 15, 15.001, 15],
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
        indicationValue: 15.003,
        unit: "kg",
      },
    ],
    linearityPoints: [
      {
        pointLabel: "50%",
        sequence: "ascending",
        appliedLoadValue: 15,
        referenceValue: 15,
        conventionalMassErrorValue: 0.001,
        indicationValue: 15.002,
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

  assert.equal(analysis.unit, "kg");
  assert.equal(analysis.completeness.readyForMetrologyReview, true);
  assert.equal(analysis.repeatability.runCount, 1);
  assert.equal(
    Number((analysis.repeatability.maxStandardDeviation ?? 0).toFixed(6)),
    0.000548,
  );
  assert.equal(Number((analysis.eccentricity?.maxAbsoluteDelta ?? 0).toFixed(6)), 0.003);
  assert.equal(Number((analysis.linearity?.maxAbsoluteError ?? 0).toFixed(6)), 0.001);
  assert.match(analysis.summary.repeatabilityLabel, /smax=/);
  assert.match(analysis.summary.eccentricityLabel, /Delta max=/);
  assert.match(analysis.summary.linearityLabel, /Erro max=/);
});

test("fails closed in the analysis output when raw measurements use mixed units", () => {
  const analysis = analyzeRawMeasurementData({
    captureMode: "manual",
    repeatabilityRuns: [
      {
        loadValue: 10,
        unit: "kg",
        indications: [10, 10.001],
      },
    ],
    eccentricityPoints: [
      {
        positionLabel: "centro",
        loadValue: 10,
        indicationValue: 10,
        unit: "g",
      },
      {
        positionLabel: "esquerda",
        loadValue: 10,
        indicationValue: 10.002,
        unit: "g",
      },
    ],
    linearityPoints: [],
    evidenceAttachments: [],
  });

  assert.equal(analysis.completeness.readyForMetrologyReview, false);
  assert.match(analysis.blockers.join(" "), /Unidades mistas/i);
  assert.equal(analysis.unit, undefined);
});

test("marks eccentricity as blocked when no central position is available", () => {
  const analysis = analyzeRawMeasurementData({
    captureMode: "manual",
    repeatabilityRuns: [],
    eccentricityPoints: [
      {
        positionLabel: "frontal",
        loadValue: 10,
        indicationValue: 10.002,
        unit: "kg",
      },
      {
        positionLabel: "traseira",
        loadValue: 10,
        indicationValue: 10.001,
        unit: "kg",
      },
    ],
    linearityPoints: [],
    evidenceAttachments: [],
  });

  assert.equal(analysis.eccentricity, undefined);
  assert.match(analysis.blockers.join(" "), /ponto central/i);
});

test("uses contextual conventional mass error when the linearity point does not provide one", () => {
  const analysis = analyzeRawMeasurementData(
    {
      captureMode: "manual",
      repeatabilityRuns: [],
      eccentricityPoints: [],
      linearityPoints: [
        {
          pointLabel: "50%",
          appliedLoadValue: 15,
          referenceValue: 15,
          indicationValue: 15.002,
          unit: "kg",
        },
      ],
      evidenceAttachments: [],
    },
    {
      defaultConventionalMassErrorValue: 0.001,
      expectedMeasurementUnit: "kg",
    },
  );

  assert.equal(Number((analysis.linearity?.maxAbsoluteError ?? 0).toFixed(6)), 0.001);
});

test("fails closed when the raw unit diverges from the expected metrology snapshot unit", () => {
  const analysis = analyzeRawMeasurementData(
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
      linearityPoints: [],
      evidenceAttachments: [],
    },
    {
      expectedMeasurementUnit: "kg",
    },
  );

  assert.match(analysis.blockers.join(" "), /unidade esperada/i);
  assert.equal(analysis.completeness.readyForMetrologyReview, false);
});
