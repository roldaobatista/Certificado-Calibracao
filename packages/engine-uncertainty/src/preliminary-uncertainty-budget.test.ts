import assert from "node:assert/strict";
import { test } from "node:test";

import { buildPreliminaryUncertaintyBudget } from "./preliminary-uncertainty-budget.js";
import { analyzeRawMeasurementData } from "./raw-measurement-analysis.js";

test("builds a complete preliminary budget from raw analysis and metrology snapshots", () => {
  const rawAnalysis = analyzeRawMeasurementData({
    captureMode: "manual",
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
        indicationValue: 15.002,
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

  const budget = buildPreliminaryUncertaintyBudget(rawAnalysis, {
    readabilityValue: 0.05,
    standardExpandedUncertaintyValue: 0.000008,
    standardCoverageFactorK: 2,
    expectedMeasurementUnit: "kg",
  });

  assert.equal(budget.readyForIndicativeUse, true);
  assert.equal(budget.repeatabilityFloorApplied, true);
  assert.equal(Number((budget.repeatabilityFloorValue ?? 0).toFixed(6)), 0.0205);
  assert.equal(
    Number((budget.components.find((component) => component.id === "repeatability")?.value ?? 0).toFixed(6)),
    0.0205,
  );
  assert.equal(
    Number((budget.components.find((component) => component.id === "resolution_zero")?.value ?? 0).toFixed(6)),
    0.014434,
  );
  assert.equal(
    Number((budget.components.find((component) => component.id === "standard_reference")?.value ?? 0).toFixed(6)),
    0.000004,
  );
  assert.equal(Number((budget.combinedStandardUncertainty?.value ?? 0).toFixed(6)), 0.02893);
  assert.equal(Number((budget.expandedUncertainty?.value ?? 0).toFixed(6)), 0.057859);
  assert.equal(budget.expandedUncertainty?.coverageFactor, 2);
  assert.match(budget.summaryLabel, /U preliminar=/);
  assert.match(budget.summaryLabel, /piso 0.41\*d aplicado/);
});

test("keeps the preliminary budget partial when the metrology snapshots are incomplete", () => {
  const rawAnalysis = analyzeRawMeasurementData({
    captureMode: "manual",
    repeatabilityRuns: [
      {
        loadValue: 5,
        unit: "kg",
        indications: [5, 5.001, 5.001, 5],
      },
    ],
    eccentricityPoints: [],
    linearityPoints: [],
    evidenceAttachments: [],
  });

  const budget = buildPreliminaryUncertaintyBudget(rawAnalysis, {
    expectedMeasurementUnit: "kg",
  });

  assert.equal(budget.readyForIndicativeUse, false);
  assert.equal(budget.combinedStandardUncertainty, undefined);
  assert.match(budget.summaryLabel, /parcial/i);
  assert.match(budget.warnings.join(" "), /snapshot do equipamento sem d/i);
  assert.match(budget.warnings.join(" "), /snapshot do padrao principal sem U e k/i);
});

test("fails closed when the raw analysis is already incoherent", () => {
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
      linearityPoints: [],
      evidenceAttachments: [],
    },
    {
      expectedMeasurementUnit: "kg",
    },
  );

  const budget = buildPreliminaryUncertaintyBudget(rawAnalysis, {
    readabilityValue: 0.001,
    expectedMeasurementUnit: "kg",
  });

  assert.equal(budget.readyForIndicativeUse, false);
  assert.equal(budget.combinedStandardUncertainty, undefined);
  assert.match(budget.blockers.join(" "), /unidade esperada/i);
  assert.match(budget.summaryLabel, /bloqueado/i);
});
