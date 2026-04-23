import type { RawMeasurementAnalysis } from "./raw-measurement-analysis.js";

export type PreliminaryUncertaintyBudgetContext = {
  readabilityValue?: number;
  standardExpandedUncertaintyValue?: number;
  standardCoverageFactorK?: number;
  expectedMeasurementUnit?: string;
  expandedCoverageFactor?: number;
};

export type PreliminaryUncertaintyComponentId =
  | "resolution_zero"
  | "resolution_load"
  | "repeatability"
  | "standard_reference";

export type PreliminaryUncertaintyComponentStatus =
  | "derived"
  | "floor_applied"
  | "missing";

export type PreliminaryUncertaintyComponent = {
  id: PreliminaryUncertaintyComponentId;
  label: string;
  status: PreliminaryUncertaintyComponentStatus;
  unit?: string;
  value?: number;
  formattedValue: string;
  detail: string;
};

export type PreliminaryUncertaintyBudget = {
  unit?: string;
  components: PreliminaryUncertaintyComponent[];
  combinedStandardUncertainty?: {
    value: number;
    unit: string;
    formatted: string;
  };
  expandedUncertainty?: {
    value: number;
    unit: string;
    coverageFactor: number;
    formatted: string;
    coverageFactorFormatted: string;
  };
  repeatabilityFloorValue?: number;
  repeatabilityFloorApplied: boolean;
  readyForIndicativeUse: boolean;
  warnings: string[];
  blockers: string[];
  summaryLabel: string;
};

export function buildPreliminaryUncertaintyBudget(
  rawAnalysis: RawMeasurementAnalysis,
  context: PreliminaryUncertaintyBudgetContext = {},
): PreliminaryUncertaintyBudget {
  const warnings: string[] = [];
  const blockers = [...rawAnalysis.blockers];
  const expectedMeasurementUnit = normalizeOptionalString(context.expectedMeasurementUnit);
  const unit = rawAnalysis.unit ?? expectedMeasurementUnit;

  const readabilityValue = normalizePositiveNumber(context.readabilityValue, "invalid_readability_value");
  const standardExpandedUncertaintyValue = normalizeNonNegativeNumber(
    context.standardExpandedUncertaintyValue,
    "invalid_standard_expanded_uncertainty_value",
  );
  const standardCoverageFactorK = normalizePositiveNumber(
    context.standardCoverageFactorK,
    "invalid_standard_coverage_factor",
  );
  const expandedCoverageFactor =
    normalizePositiveNumber(
      context.expandedCoverageFactor ?? 2,
      "invalid_expanded_coverage_factor",
    ) ?? 2;

  if (!unit) {
    warnings.push("Unidade metrologica ainda nao consolidada para o orcamento preliminar.");
  }

  if (readabilityValue === undefined) {
    warnings.push("Snapshot do equipamento sem d para componentes de resolucao.");
  }

  if (
    standardExpandedUncertaintyValue === undefined &&
    standardCoverageFactorK === undefined
  ) {
    warnings.push("Snapshot do padrao principal sem U e k para derivar u_mc.");
  } else if (
    standardExpandedUncertaintyValue === undefined ||
    standardCoverageFactorK === undefined
  ) {
    warnings.push("Snapshot do padrao principal incompleto para derivar u_mc.");
  }

  const observedRepeatabilityValue =
    rawAnalysis.repeatability.maxStandardDeviation ??
    rawAnalysis.repeatability.representativeStandardDeviation;
  if (observedRepeatabilityValue === undefined) {
    blockers.push("Sem repetitividade estruturada para orcamento preliminar.");
  }

  const repeatabilityFloorValue =
    readabilityValue !== undefined ? 0.41 * readabilityValue : undefined;
  const repeatabilityFloorApplied =
    observedRepeatabilityValue !== undefined &&
    repeatabilityFloorValue !== undefined &&
    observedRepeatabilityValue < repeatabilityFloorValue;
  const effectiveRepeatabilityValue =
    observedRepeatabilityValue === undefined
      ? undefined
      : repeatabilityFloorApplied
        ? repeatabilityFloorValue
        : observedRepeatabilityValue;

  const resolutionZeroValue =
    readabilityValue !== undefined ? readabilityValue / Math.sqrt(12) : undefined;
  const resolutionLoadValue =
    readabilityValue !== undefined ? readabilityValue / Math.sqrt(12) : undefined;
  const standardReferenceValue =
    standardExpandedUncertaintyValue !== undefined && standardCoverageFactorK !== undefined
      ? standardExpandedUncertaintyValue / standardCoverageFactorK
      : undefined;

  const components: PreliminaryUncertaintyComponent[] = [
    buildDerivedComponent({
      id: "resolution_zero",
      label: "u_d0",
      value: resolutionZeroValue,
      unit,
      detail:
        readabilityValue !== undefined
          ? `u_d0 = d / sqrt(12) com d=${formatValue(readabilityValue)} ${unit ?? ""}`.trim()
          : "Indisponivel sem snapshot de d do equipamento.",
    }),
    buildDerivedComponent({
      id: "resolution_load",
      label: "u_dL",
      value: resolutionLoadValue,
      unit,
      detail:
        readabilityValue !== undefined
          ? `u_dL = d / sqrt(12) com d=${formatValue(readabilityValue)} ${unit ?? ""}`.trim()
          : "Indisponivel sem snapshot de d do equipamento.",
    }),
    {
      id: "repeatability",
      label: "u_rep",
      status:
        effectiveRepeatabilityValue === undefined
          ? "missing"
          : repeatabilityFloorApplied
            ? "floor_applied"
            : "derived",
      unit,
      value: effectiveRepeatabilityValue,
      formattedValue: formatComponentValue(effectiveRepeatabilityValue, unit),
      detail:
        effectiveRepeatabilityValue === undefined
          ? "Indisponivel sem serie de repetitividade."
          : repeatabilityFloorApplied && repeatabilityFloorValue !== undefined
            ? `smax=${formatValue(observedRepeatabilityValue!)} ${unit ?? ""} ficou abaixo de 0.41*d=${formatValue(
                repeatabilityFloorValue,
              )} ${unit ?? ""}; piso aplicado.`.trim()
            : `Usa smax=${formatValue(observedRepeatabilityValue!)} ${unit ?? ""} da repetitividade estruturada.`.trim(),
    },
    buildDerivedComponent({
      id: "standard_reference",
      label: "u_mc",
      value: standardReferenceValue,
      unit,
      detail:
        standardReferenceValue !== undefined
          ? `u_mc = U / k com U=${formatValue(standardExpandedUncertaintyValue!)} ${unit ?? ""} e k=${formatValue(
              standardCoverageFactorK!,
            )}`.trim()
          : "Indisponivel sem snapshot completo de U e k do padrao principal.",
    }),
  ];

  const derivedValues = components
    .map((component) => component.value)
    .filter((value): value is number => value !== undefined);
  const combinedStandardUncertainty =
    blockers.length === 0 && components.every((component) => component.value !== undefined) && unit
      ? buildCombinedStandardUncertainty(derivedValues, unit)
      : undefined;
  const expandedUncertainty =
    combinedStandardUncertainty && blockers.length === 0
      ? {
          value: combinedStandardUncertainty.value * expandedCoverageFactor,
          unit: combinedStandardUncertainty.unit,
          coverageFactor: expandedCoverageFactor,
          formatted: `${formatValue(
            combinedStandardUncertainty.value * expandedCoverageFactor,
          )} ${combinedStandardUncertainty.unit}`,
          coverageFactorFormatted: `k=${formatValue(expandedCoverageFactor)}`,
        }
      : undefined;

  const readyForIndicativeUse =
    blockers.length === 0 &&
    combinedStandardUncertainty !== undefined &&
    components.every((component) => component.value !== undefined);

  const uniqueBlockers = uniqueStrings(blockers);
  const uniqueWarnings = uniqueStrings(warnings);

  return {
    unit,
    components,
    combinedStandardUncertainty,
    expandedUncertainty,
    repeatabilityFloorValue,
    repeatabilityFloorApplied,
    readyForIndicativeUse,
    warnings: uniqueWarnings,
    blockers: uniqueBlockers,
    summaryLabel: buildSummaryLabel({
      unit,
      components,
      combinedStandardUncertainty,
      expandedUncertainty,
      repeatabilityFloorApplied,
      warnings: uniqueWarnings,
      blockers: uniqueBlockers,
      readyForIndicativeUse,
    }),
  };
}

function buildDerivedComponent(input: {
  id: PreliminaryUncertaintyComponentId;
  label: string;
  value: number | undefined;
  unit: string | undefined;
  detail: string;
}): PreliminaryUncertaintyComponent {
  return {
    id: input.id,
    label: input.label,
    status: input.value === undefined ? "missing" : "derived",
    unit: input.unit,
    value: input.value,
    formattedValue: formatComponentValue(input.value, input.unit),
    detail: input.detail,
  };
}

function buildCombinedStandardUncertainty(values: number[], unit: string) {
  const value = Math.sqrt(values.reduce((sum, componentValue) => sum + componentValue ** 2, 0));

  return {
    value,
    unit,
    formatted: `${formatValue(value)} ${unit}`,
  };
}

function buildSummaryLabel(input: {
  unit?: string;
  components: PreliminaryUncertaintyComponent[];
  combinedStandardUncertainty?: PreliminaryUncertaintyBudget["combinedStandardUncertainty"];
  expandedUncertainty?: PreliminaryUncertaintyBudget["expandedUncertainty"];
  repeatabilityFloorApplied: boolean;
  warnings: string[];
  blockers: string[];
  readyForIndicativeUse: boolean;
}) {
  if (
    input.readyForIndicativeUse &&
    input.combinedStandardUncertainty &&
    input.expandedUncertainty
  ) {
    const componentSummary = input.components
      .map((component) => `${component.label}=${component.formattedValue}`)
      .join(" | ");

    return `U preliminar=${input.expandedUncertainty.formatted} (${input.expandedUncertainty.coverageFactorFormatted}) | Uc=${input.combinedStandardUncertainty.formatted} | ${componentSummary}${
      input.repeatabilityFloorApplied ? " | piso 0.41*d aplicado" : ""
    }`;
  }

  if (input.blockers.length > 0) {
    return `Orcamento preliminar bloqueado: ${input.blockers.join("; ")}`;
  }

  if (input.warnings.length > 0) {
    return `Orcamento preliminar parcial: ${input.warnings.join("; ")}`;
  }

  return `Orcamento preliminar em consolidacao${input.unit ? ` (${input.unit})` : ""}.`;
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

function normalizeNonNegativeNumber(value: number | undefined, code: string) {
  if (value === undefined) {
    return undefined;
  }

  if (!Number.isFinite(value) || value < 0) {
    throw new Error(code);
  }

  return value;
}

function formatComponentValue(value: number | undefined, unit: string | undefined) {
  if (value === undefined) {
    return "Indisponivel";
  }

  return `${formatValue(value)}${unit ? ` ${unit}` : ""}`;
}

function formatValue(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(6).replace(/\.?0+$/, "");
}

function uniqueStrings(values: string[]) {
  return Array.from(new Set(values));
}
