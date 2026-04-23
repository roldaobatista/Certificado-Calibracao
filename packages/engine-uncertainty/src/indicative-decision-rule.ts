import type { PreliminaryUncertaintyBudget } from "./preliminary-uncertainty-budget.js";
import type { Portaria157IndicativeToleranceEvaluation } from "./portaria-157-indicative-tolerance.js";

export type IndicativeDecisionMode = "simple_tolerance" | "guard_band";
export type IndicativeDecisionVerdict = "conforming" | "non_conforming" | "inconclusive";

export type IndicativeDecisionPointEvaluation = {
  pointLabel: string;
  absoluteErrorValue: number;
  toleranceValue: number;
  unit: string;
  verdict: IndicativeDecisionVerdict;
};

export type IndicativeDecisionEvaluation = {
  mode?: IndicativeDecisionMode;
  verdict?: IndicativeDecisionVerdict;
  expandedUncertaintyValue?: number;
  unit?: string;
  readyForIndicativeUse: boolean;
  points: IndicativeDecisionPointEvaluation[];
  warnings: string[];
  blockers: string[];
  summaryLabel: string;
};

export function evaluateIndicativeDecisionRule(input: {
  decisionRuleLabel?: string;
  preliminaryUncertainty?: PreliminaryUncertaintyBudget;
  indicativeTolerance?: Portaria157IndicativeToleranceEvaluation;
}): IndicativeDecisionEvaluation {
  const warnings = uniqueStrings([
    ...(input.preliminaryUncertainty?.warnings ?? []),
    ...(input.indicativeTolerance?.warnings ?? []),
  ]);
  const blockers = uniqueStrings([
    ...(input.indicativeTolerance?.blockers ?? []),
  ]);
  const mode = resolveMode(input.decisionRuleLabel);

  if (!mode) {
    warnings.push("Regra de decisao oficial ainda nao identificada para avaliacao indicativa.");
  }

  const tolerancePoints = input.indicativeTolerance?.points ?? [];
  if (tolerancePoints.length === 0) {
    warnings.push("Sem pontos avaliados de EMA para decisao indicativa.");
  }

  const unit = input.indicativeTolerance?.unit ?? input.preliminaryUncertainty?.unit;
  const expandedUncertaintyValue = input.preliminaryUncertainty?.expandedUncertainty?.value;

  if (mode === "guard_band" && expandedUncertaintyValue === undefined) {
    warnings.push("U preliminar indisponivel para aplicar banda de guarda indicativa.");
  }

  const points =
    mode &&
    tolerancePoints.length > 0 &&
    (mode !== "guard_band" || expandedUncertaintyValue !== undefined)
      ? tolerancePoints.map((point) => {
          const absoluteErrorValue = Math.abs(point.errorValue);
          const toleranceValue = point.toleranceValue;
          const verdict: IndicativeDecisionVerdict =
            mode === "simple_tolerance"
              ? absoluteErrorValue <= toleranceValue
                ? "conforming"
                : "non_conforming"
              : absoluteErrorValue + expandedUncertaintyValue! <= toleranceValue
                ? "conforming"
                : absoluteErrorValue - expandedUncertaintyValue! > toleranceValue
                  ? "non_conforming"
                  : "inconclusive";

          return {
            pointLabel: point.pointLabel,
            absoluteErrorValue,
            toleranceValue,
            unit: point.unit,
            verdict,
          };
        })
      : [];

  const verdict =
    points.length === 0
      ? undefined
      : points.some((point) => point.verdict === "non_conforming")
        ? "non_conforming"
        : points.some((point) => point.verdict === "inconclusive")
          ? "inconclusive"
          : "conforming";

  const readyForIndicativeUse =
    blockers.length === 0 &&
    Boolean(mode) &&
    points.length > 0 &&
    verdict !== undefined;

  const uniqueWarnings = uniqueStrings(warnings);
  const uniqueBlockers = uniqueStrings(blockers);

  return {
    mode,
    verdict,
    expandedUncertaintyValue,
    unit,
    readyForIndicativeUse,
    points,
    warnings: uniqueWarnings,
    blockers: uniqueBlockers,
    summaryLabel: buildSummaryLabel({
      mode,
      verdict,
      unit,
      expandedUncertaintyValue,
      warnings: uniqueWarnings,
      blockers: uniqueBlockers,
      pointCount: points.length,
    }),
  };
}

function resolveMode(value: string | undefined): IndicativeDecisionMode | undefined {
  const normalized = value?.trim().toLowerCase();
  if (!normalized) {
    return undefined;
  }

  if (normalized.includes("sem banda de guarda")) {
    return "simple_tolerance";
  }

  if (normalized.includes("com banda de guarda") || normalized.includes("banda de guarda")) {
    return "guard_band";
  }

  return undefined;
}

function buildSummaryLabel(input: {
  mode?: IndicativeDecisionMode;
  verdict?: IndicativeDecisionVerdict;
  unit?: string;
  expandedUncertaintyValue?: number;
  warnings: string[];
  blockers: string[];
  pointCount: number;
}) {
  if (input.blockers.length > 0) {
    return `Decisao indicativa bloqueada: ${input.blockers.join("; ")}`;
  }

  if (input.mode && input.verdict) {
    const modeLabel =
      input.mode === "guard_band"
        ? `banda de guarda${input.expandedUncertaintyValue !== undefined ? ` com U=${formatValue(input.expandedUncertaintyValue)} ${input.unit ?? ""}` : ""}`.trim()
        : "sem banda de guarda";
    const verdictLabel =
      input.verdict === "conforming"
        ? "conforme"
        : input.verdict === "non_conforming"
          ? "nao conforme"
          : "inconclusiva";

    return `Decisao indicativa ${verdictLabel} em ${input.pointCount} ponto(s) (${modeLabel}).`;
  }

  if (input.warnings.length > 0) {
    return `Decisao indicativa parcial: ${input.warnings.join("; ")}`;
  }

  return "Decisao indicativa em consolidacao.";
}

function formatValue(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(6).replace(/\.?0+$/, "");
}

function uniqueStrings(values: string[]) {
  return Array.from(new Set(values));
}
