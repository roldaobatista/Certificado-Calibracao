import type { RawMeasurementAnalysis } from "./raw-measurement-analysis.js";

type EquipmentInstrumentKind =
  | "nawi"
  | "analytical_balance"
  | "precision_balance"
  | "platform_scale"
  | "vehicle_scale";

type EquipmentNormativeClass = "i" | "ii" | "iii" | "iiii";

export type Portaria157IndicativeToleranceContext = {
  instrumentKind?: EquipmentInstrumentKind;
  normativeClass?: EquipmentNormativeClass;
  verificationScaleIntervalValue?: number;
  maximumCapacityValue?: number;
  expectedMeasurementUnit?: string;
};

export type Portaria157IndicativePointEvaluation = {
  pointLabel: string;
  appliedLoadValue: number;
  errorValue: number;
  unit: string;
  loadInVerificationIntervals: number;
  emaMultiplier: 1 | 2 | 3;
  toleranceValue: number;
  withinTolerance: boolean;
};

export type Portaria157IndicativeToleranceEvaluation = {
  unit?: string;
  classLabel?: string;
  verificationScaleIntervalValue?: number;
  readyForIndicativeUse: boolean;
  evaluatedPointCount: number;
  failingPointCount: number;
  points: Portaria157IndicativePointEvaluation[];
  warnings: string[];
  blockers: string[];
  summaryLabel: string;
};

export function evaluatePortaria157IndicativeTolerance(
  rawAnalysis: RawMeasurementAnalysis,
  context: Portaria157IndicativeToleranceContext = {},
): Portaria157IndicativeToleranceEvaluation {
  const warnings: string[] = [];
  const blockers = [...rawAnalysis.blockers];
  const unit = rawAnalysis.linearity?.unit ?? rawAnalysis.unit ?? normalizeOptionalString(context.expectedMeasurementUnit);
  const normativeClass = context.normativeClass;
  const verificationScaleIntervalValue = normalizePositiveNumber(
    context.verificationScaleIntervalValue,
    "invalid_verification_scale_interval",
  );

  if (!rawAnalysis.linearity || rawAnalysis.linearity.points.length === 0) {
    warnings.push("Sem linearidade estruturada para avaliar EMA indicativo.");
  }

  if (!normativeClass) {
    warnings.push("Snapshot do equipamento sem classe normativa para EMA indicativo.");
  }

  if (verificationScaleIntervalValue === undefined) {
    warnings.push("Snapshot do equipamento sem e para EMA indicativo.");
  }

  if (!unit) {
    warnings.push("Unidade nao consolidada para EMA indicativo.");
  }

  const points =
    rawAnalysis.linearity &&
    normativeClass &&
    verificationScaleIntervalValue !== undefined &&
    unit
      ? rawAnalysis.linearity.points.map((point) =>
          evaluatePoint(point, normativeClass, verificationScaleIntervalValue, unit),
        )
      : [];

  const failingPointCount = points.filter((point) => !point.withinTolerance).length;
  if (failingPointCount > 0) {
    blockers.push(
      `${failingPointCount} ponto(s) de linearidade fora do EMA indicativo da Portaria 157/2022.`,
    );
  }

  const readyForIndicativeUse =
    blockers.length === 0 &&
    points.length > 0 &&
    Boolean(normativeClass) &&
    verificationScaleIntervalValue !== undefined;

  const uniqueWarnings = uniqueStrings(warnings);
  const uniqueBlockers = uniqueStrings(blockers);

  return {
    unit,
    classLabel: normativeClass?.toUpperCase(),
    verificationScaleIntervalValue,
    readyForIndicativeUse,
    evaluatedPointCount: points.length,
    failingPointCount,
    points,
    warnings: uniqueWarnings,
    blockers: uniqueBlockers,
    summaryLabel: buildSummaryLabel({
      points,
      warnings: uniqueWarnings,
      blockers: uniqueBlockers,
      normativeClass,
      verificationScaleIntervalValue,
      unit,
    }),
  };
}

function evaluatePoint(
  point: NonNullable<RawMeasurementAnalysis["linearity"]>["points"][number],
  normativeClass: EquipmentNormativeClass,
  verificationScaleIntervalValue: number,
  unit: string,
): Portaria157IndicativePointEvaluation {
  const loadInVerificationIntervals = Math.abs(point.appliedLoadValue) / verificationScaleIntervalValue;
  const emaMultiplier = resolveEmaMultiplier(normativeClass, loadInVerificationIntervals);
  const toleranceValue = emaMultiplier * verificationScaleIntervalValue;
  const withinTolerance = Math.abs(point.errorValue) <= toleranceValue;

  return {
    pointLabel: point.pointLabel,
    appliedLoadValue: point.appliedLoadValue,
    errorValue: point.errorValue,
    unit,
    loadInVerificationIntervals,
    emaMultiplier,
    toleranceValue,
    withinTolerance,
  };
}

function resolveEmaMultiplier(
  normativeClass: EquipmentNormativeClass,
  loadInVerificationIntervals: number,
): 1 | 2 | 3 {
  switch (normativeClass) {
    case "i":
      if (loadInVerificationIntervals <= 50_000) return 1;
      if (loadInVerificationIntervals <= 200_000) return 2;
      return 3;
    case "ii":
      if (loadInVerificationIntervals <= 5_000) return 1;
      if (loadInVerificationIntervals <= 20_000) return 2;
      return 3;
    case "iii":
      if (loadInVerificationIntervals <= 500) return 1;
      if (loadInVerificationIntervals <= 2_000) return 2;
      return 3;
    case "iiii":
      if (loadInVerificationIntervals <= 50) return 1;
      if (loadInVerificationIntervals <= 200) return 2;
      return 3;
    default:
      return 3;
  }
}

function buildSummaryLabel(input: {
  points: Portaria157IndicativePointEvaluation[];
  warnings: string[];
  blockers: string[];
  normativeClass?: EquipmentNormativeClass;
  verificationScaleIntervalValue?: number;
  unit?: string;
}) {
  if (input.blockers.length > 0) {
    return `EMA indicativo bloqueado: ${input.blockers.join("; ")}`;
  }

  if (input.points.length > 0 && input.normativeClass && input.verificationScaleIntervalValue !== undefined) {
    const worstPoint = input.points.find((point) => !point.withinTolerance) ?? input.points[0]!;
    const passLabel = input.points.every((point) => point.withinTolerance)
      ? "Todos os pontos dentro do EMA"
      : "Ha ponto(s) fora do EMA";

    return `${passLabel} · classe ${input.normativeClass.toUpperCase()} · e=${formatValue(
      input.verificationScaleIntervalValue,
    )} ${input.unit ?? ""} · pior ponto ${worstPoint.pointLabel} com |erro|=${formatValue(
      Math.abs(worstPoint.errorValue),
    )} ${worstPoint.unit} vs EMA=${formatValue(worstPoint.toleranceValue)} ${worstPoint.unit}`.trim();
  }

  if (input.warnings.length > 0) {
    return `EMA indicativo parcial: ${input.warnings.join("; ")}`;
  }

  return "EMA indicativo em consolidacao.";
}

function normalizeOptionalString(value: string | undefined) {
  const normalized = value?.trim();
  return normalized ? normalized : undefined;
}

function normalizePositiveNumber(value: number | undefined, code: string) {
  if (value === undefined) {
    return undefined;
  }

  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(code);
  }

  return value;
}

function formatValue(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(6).replace(/\.?0+$/, "");
}

function uniqueStrings(values: string[]) {
  return Array.from(new Set(values));
}
