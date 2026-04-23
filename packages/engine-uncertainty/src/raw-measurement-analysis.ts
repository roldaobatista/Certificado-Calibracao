export type RawCaptureMode = "manual" | "imported" | "hybrid";

export type RawEnvironmentalSnapshotInput = {
  temperatureStartC: number;
  temperatureEndC: number;
  relativeHumidityPercent: number;
  atmosphericPressureHpa?: number;
  notes?: string;
};

export type RawRepeatabilityRunInput = {
  loadValue: number;
  unit: string;
  indications: number[];
  notes?: string;
};

export type RawEccentricityPointInput = {
  positionLabel: string;
  loadValue: number;
  indicationValue: number;
  unit: string;
  notes?: string;
};

export type RawLinearityPointInput = {
  pointLabel: string;
  sequence?: "ascending" | "descending";
  appliedLoadValue: number;
  referenceValue: number;
  indicationValue: number;
  unit: string;
  conventionalMassErrorValue?: number;
  notes?: string;
};

export type RawEvidenceAttachmentInput = {
  attachmentId: string;
  label: string;
  kind: string;
  mediaType: string;
  storageKey?: string;
  sha256?: string;
  capturedAtUtc?: string;
};

export type RawMeasurementAnalysisInput = {
  captureMode: RawCaptureMode;
  performedAtUtc?: string;
  environment?: RawEnvironmentalSnapshotInput;
  repeatabilityRuns: RawRepeatabilityRunInput[];
  eccentricityPoints: RawEccentricityPointInput[];
  linearityPoints: RawLinearityPointInput[];
  hysteresisPoints?: RawLinearityPointInput[];
  evidenceAttachments: RawEvidenceAttachmentInput[];
  notes?: string;
};

export type RawMeasurementAnalysisContext = {
  defaultConventionalMassErrorValue?: number;
  expectedMeasurementUnit?: string;
};

export type RepeatabilityRunAnalysis = {
  loadValue: number;
  unit: string;
  repetitions: number;
  meanValue: number;
  standardDeviation: number;
  minimumValue: number;
  maximumValue: number;
};

export type EccentricityAnalysis = {
  unit: string;
  centerValue: number;
  maxAbsoluteDelta: number;
  worstPositionLabel?: string;
  pointCount: number;
};

export type LinearityPointAnalysis = {
  pointLabel: string;
  sequence?: "ascending" | "descending";
  appliedLoadValue: number;
  referenceValue: number;
  effectiveReferenceValue: number;
  indicationValue: number;
  errorValue: number;
  unit: string;
};

export type LinearityAnalysis = {
  unit: string;
  pointCount: number;
  maxAbsoluteError: number;
  worstPointLabel?: string;
  points: LinearityPointAnalysis[];
};

export type RawMeasurementAnalysis = {
  captureMode: RawCaptureMode;
  unit?: string;
  evidenceAttachmentCount: number;
  environment?: RawEnvironmentalSnapshotInput & {
    temperatureSpanC: number;
  };
  completeness: {
    hasRepeatability: boolean;
    hasEccentricity: boolean;
    hasLinearity: boolean;
    hasEvidence: boolean;
    readyForMetrologyReview: boolean;
  };
  repeatability: {
    runCount: number;
    representativeStandardDeviation?: number;
    maxStandardDeviation?: number;
    runs: RepeatabilityRunAnalysis[];
  };
  eccentricity?: EccentricityAnalysis;
  linearity?: LinearityAnalysis;
  warnings: string[];
  blockers: string[];
  summary: {
    repeatabilityLabel: string;
    eccentricityLabel: string;
    linearityLabel: string;
    completenessLabel: string;
    unitLabel: string;
  };
};

export function analyzeRawMeasurementData(
  input: RawMeasurementAnalysisInput,
  context: RawMeasurementAnalysisContext = {},
): RawMeasurementAnalysis {
  const warnings: string[] = [];
  const blockers: string[] = [];
  const unitSet = collectUnits(input);
  const unit = unitSet.size === 1 ? unitSet.values().next().value : undefined;

  if (unitSet.size > 1) {
    blockers.push("Unidades mistas entre os ensaios brutos.");
  }
  if (
    context.expectedMeasurementUnit &&
    unit &&
    context.expectedMeasurementUnit.trim() !== unit
  ) {
    blockers.push("Unidade do bruto diverge da unidade esperada no snapshot metrologico.");
  }

  if (input.repeatabilityRuns.length === 0) {
    warnings.push("Ensaio de repetitividade ausente.");
  }
  if (input.eccentricityPoints.length === 0) {
    warnings.push("Ensaio de excentricidade ausente.");
  }
  if (input.linearityPoints.length === 0) {
    warnings.push("Ensaio de linearidade ausente.");
  }
  if (input.evidenceAttachments.length === 0) {
    warnings.push("Sem evidencias estruturadas vinculadas ao bruto.");
  }

  const repeatabilityRuns = input.repeatabilityRuns.map(analyzeRepeatabilityRun);
  const maxStandardDeviation =
    repeatabilityRuns.length > 0
      ? Math.max(...repeatabilityRuns.map((run) => run.standardDeviation))
      : undefined;
  const representativeStandardDeviation =
    repeatabilityRuns.length > 0
      ? repeatabilityRuns.reduce((sum, run) => sum + run.standardDeviation, 0) /
        repeatabilityRuns.length
      : undefined;

  const eccentricity = analyzeEccentricity(input.eccentricityPoints, blockers);
  const linearity = analyzeLinearity(input.linearityPoints, context);

  const readyForMetrologyReview =
    blockers.length === 0 &&
    repeatabilityRuns.length > 0 &&
    Boolean(eccentricity) &&
    Boolean(linearity) &&
    input.evidenceAttachments.length > 0;

  return {
    captureMode: input.captureMode,
    unit,
    evidenceAttachmentCount: input.evidenceAttachments.length,
    environment: input.environment
      ? {
          ...input.environment,
          temperatureSpanC: Math.abs(
            input.environment.temperatureEndC - input.environment.temperatureStartC,
          ),
        }
      : undefined,
    completeness: {
      hasRepeatability: repeatabilityRuns.length > 0,
      hasEccentricity: Boolean(eccentricity),
      hasLinearity: Boolean(linearity),
      hasEvidence: input.evidenceAttachments.length > 0,
      readyForMetrologyReview,
    },
    repeatability: {
      runCount: repeatabilityRuns.length,
      representativeStandardDeviation,
      maxStandardDeviation,
      runs: repeatabilityRuns,
    },
    eccentricity,
    linearity,
    warnings,
    blockers,
    summary: {
      repeatabilityLabel:
        repeatabilityRuns.length > 0 && maxStandardDeviation !== undefined
          ? `smax=${formatValue(maxStandardDeviation)} ${unit ?? repeatabilityRuns[0]!.unit} em ${repeatabilityRuns.length} serie(s)`
          : "Sem repetitividade estruturada",
      eccentricityLabel: eccentricity
        ? `Delta max=${formatValue(eccentricity.maxAbsoluteDelta)} ${eccentricity.unit} em ${eccentricity.worstPositionLabel ?? "ponto sem rotulo"}`
        : "Sem excentricidade estruturada",
      linearityLabel: linearity
        ? `Erro max=${formatValue(linearity.maxAbsoluteError)} ${linearity.unit} em ${linearity.worstPointLabel ?? "ponto sem rotulo"}`
        : "Sem linearidade estruturada",
      completenessLabel: readyForMetrologyReview
        ? "Bruto estruturado apto para revisao"
        : blockers.length > 0
          ? `Bruto incoerente: ${blockers.join("; ")}`
          : `Bruto incompleto: ${warnings.join("; ") || "complementar ensaios"}`,
      unitLabel: unit ?? "Unidade inconsistente",
    },
  };
}

function analyzeRepeatabilityRun(
  input: RawRepeatabilityRunInput,
): RepeatabilityRunAnalysis {
  assertNonEmptyUnit(input.unit, "invalid_repeatability_unit");
  assertFiniteArray(input.indications, "invalid_repeatability_indications");

  const meanValue = input.indications.reduce((sum, value) => sum + value, 0) / input.indications.length;
  const standardDeviation =
    input.indications.length > 1
      ? Math.sqrt(
          input.indications.reduce(
            (sum, value) => sum + (value - meanValue) ** 2,
            0,
          ) /
            (input.indications.length - 1),
        )
      : 0;

  return {
    loadValue: input.loadValue,
    unit: input.unit.trim(),
    repetitions: input.indications.length,
    meanValue,
    standardDeviation,
    minimumValue: Math.min(...input.indications),
    maximumValue: Math.max(...input.indications),
  };
}

function analyzeEccentricity(
  points: RawEccentricityPointInput[],
  blockers: string[],
): EccentricityAnalysis | undefined {
  if (points.length === 0) {
    return undefined;
  }

  const centerPoints = points.filter((point) => isCenterPosition(point.positionLabel));
  if (centerPoints.length === 0) {
    blockers.push("Excentricidade sem ponto central identificado.");
    return undefined;
  }

  const centerValue =
    centerPoints.reduce((sum, point) => sum + point.indicationValue, 0) / centerPoints.length;
  const offCenterPoints = points.filter((point) => !isCenterPosition(point.positionLabel));

  if (offCenterPoints.length === 0) {
    blockers.push("Excentricidade sem pontos fora do centro.");
    return undefined;
  }

  const ranked = offCenterPoints
    .map((point) => ({
      point,
      delta: Math.abs(point.indicationValue - centerValue),
    }))
    .sort((left, right) => right.delta - left.delta);
  const worst = ranked[0]!;

  return {
    unit: offCenterPoints[0]!.unit.trim(),
    centerValue,
    maxAbsoluteDelta: worst.delta,
    worstPositionLabel: worst.point.positionLabel,
    pointCount: points.length,
  };
}

function analyzeLinearity(
  points: RawLinearityPointInput[],
  context: RawMeasurementAnalysisContext,
): LinearityAnalysis | undefined {
  if (points.length === 0) {
    return undefined;
  }

  const analyzedPoints = points.map((point) => {
    assertNonEmptyUnit(point.unit, "invalid_linearity_unit");

    const effectiveReferenceValue =
      point.referenceValue +
      (point.conventionalMassErrorValue ?? context.defaultConventionalMassErrorValue ?? 0);
    const errorValue = point.indicationValue - effectiveReferenceValue;

    return {
      pointLabel: point.pointLabel,
      sequence: point.sequence,
      appliedLoadValue: point.appliedLoadValue,
      referenceValue: point.referenceValue,
      effectiveReferenceValue,
      indicationValue: point.indicationValue,
      errorValue,
      unit: point.unit.trim(),
    };
  });

  const ranked = analyzedPoints
    .map((point) => ({
      point,
      absoluteError: Math.abs(point.errorValue),
    }))
    .sort((left, right) => right.absoluteError - left.absoluteError);
  const worst = ranked[0]!;

  return {
    unit: analyzedPoints[0]!.unit,
    pointCount: analyzedPoints.length,
    maxAbsoluteError: worst.absoluteError,
    worstPointLabel: worst.point.pointLabel,
    points: analyzedPoints,
  };
}

function collectUnits(input: RawMeasurementAnalysisInput) {
  const units = new Set<string>();

  for (const run of input.repeatabilityRuns) {
    const normalized = run.unit.trim();
    if (normalized.length > 0) {
      units.add(normalized);
    }
  }

  for (const point of input.eccentricityPoints) {
    const normalized = point.unit.trim();
    if (normalized.length > 0) {
      units.add(normalized);
    }
  }

  for (const point of input.linearityPoints) {
    const normalized = point.unit.trim();
    if (normalized.length > 0) {
      units.add(normalized);
    }
  }

  for (const point of input.hysteresisPoints ?? []) {
    const normalized = point.unit.trim();
    if (normalized.length > 0) {
      units.add(normalized);
    }
  }

  return units;
}

function isCenterPosition(value: string) {
  const normalized = value.trim().toLowerCase();
  return normalized === "centro" || normalized === "center";
}

function assertFiniteArray(values: number[], code: string) {
  if (values.length === 0 || values.some((value) => !Number.isFinite(value))) {
    throw new Error(code);
  }
}

function assertNonEmptyUnit(value: string, code: string) {
  if (value.trim().length === 0) {
    throw new Error(code);
  }
}

function formatValue(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(6).replace(/\.?0+$/, "");
}
