import assert from "node:assert/strict";
import { test } from "node:test";

import { evaluateIndicativeDecisionRule } from "./indicative-decision-rule.js";

test("evaluates a conforming indicative decision without guard band", () => {
  const evaluation = evaluateIndicativeDecisionRule({
    decisionRuleLabel: "ILAC G8 sem banda de guarda",
    indicativeTolerance: {
      unit: "kg",
      classLabel: "III",
      verificationScaleIntervalValue: 0.05,
      readyForIndicativeUse: true,
      evaluatedPointCount: 1,
      failingPointCount: 0,
      points: [
        {
          pointLabel: "50%",
          appliedLoadValue: 15,
          errorValue: 0.001,
          unit: "kg",
          loadInVerificationIntervals: 300,
          emaMultiplier: 1,
          toleranceValue: 0.05,
          withinTolerance: true,
        },
      ],
      warnings: [],
      blockers: [],
      summaryLabel: "Todos os pontos dentro do EMA.",
    },
  });

  assert.equal(evaluation.readyForIndicativeUse, true);
  assert.equal(evaluation.verdict, "conforming");
  assert.match(evaluation.summaryLabel, /conforme/i);
});

test("evaluates an inconclusive indicative decision with guard band", () => {
  const evaluation = evaluateIndicativeDecisionRule({
    decisionRuleLabel: "ILAC G8 com banda de guarda",
    preliminaryUncertainty: {
      unit: "kg",
      components: [],
      combinedStandardUncertainty: {
        value: 0.025,
        unit: "kg",
        formatted: "0.025 kg",
      },
      expandedUncertainty: {
        value: 0.05,
        unit: "kg",
        coverageFactor: 2,
        formatted: "0.05 kg",
        coverageFactorFormatted: "k=2",
      },
      repeatabilityFloorApplied: false,
      readyForIndicativeUse: true,
      warnings: [],
      blockers: [],
      summaryLabel: "U preliminar=0.05 kg",
    },
    indicativeTolerance: {
      unit: "kg",
      classLabel: "III",
      verificationScaleIntervalValue: 0.05,
      readyForIndicativeUse: true,
      evaluatedPointCount: 1,
      failingPointCount: 0,
      points: [
        {
          pointLabel: "50%",
          appliedLoadValue: 15,
          errorValue: 0.02,
          unit: "kg",
          loadInVerificationIntervals: 300,
          emaMultiplier: 1,
          toleranceValue: 0.05,
          withinTolerance: true,
        },
      ],
      warnings: [],
      blockers: [],
      summaryLabel: "Todos os pontos dentro do EMA.",
    },
  });

  assert.equal(evaluation.readyForIndicativeUse, true);
  assert.equal(evaluation.verdict, "inconclusive");
  assert.match(evaluation.summaryLabel, /inconclusiva/i);
});

test("keeps the indicative decision partial when rule label or U are missing", () => {
  const evaluation = evaluateIndicativeDecisionRule({
    indicativeTolerance: {
      unit: "kg",
      classLabel: "III",
      verificationScaleIntervalValue: 0.05,
      readyForIndicativeUse: true,
      evaluatedPointCount: 1,
      failingPointCount: 0,
      points: [
        {
          pointLabel: "50%",
          appliedLoadValue: 15,
          errorValue: 0.001,
          unit: "kg",
          loadInVerificationIntervals: 300,
          emaMultiplier: 1,
          toleranceValue: 0.05,
          withinTolerance: true,
        },
      ],
      warnings: [],
      blockers: [],
      summaryLabel: "Todos os pontos dentro do EMA.",
    },
  });

  assert.equal(evaluation.readyForIndicativeUse, false);
  assert.equal(evaluation.verdict, undefined);
  assert.match(evaluation.summaryLabel, /parcial/i);
});
