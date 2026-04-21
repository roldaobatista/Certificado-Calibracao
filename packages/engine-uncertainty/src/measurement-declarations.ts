export type CertificateMeasurementDeclaration = {
  result: {
    value: number;
    unit: string;
    formatted: string;
  };
  expandedUncertainty: {
    value: number;
    unit: string;
    formatted: string;
  };
  coverageFactor: {
    value: number;
    formatted: string;
  };
  summary: string;
};

export function buildCertificateMeasurementDeclaration(input: {
  resultValue: number;
  expandedUncertaintyValue: number;
  coverageFactor: number;
  unit: string;
}): CertificateMeasurementDeclaration {
  const unit = input.unit.trim();
  if (unit.length === 0) {
    throw new Error("missing_unit");
  }

  assertFiniteNumber(input.resultValue, "invalid_result_value");
  assertPositiveOrZero(input.expandedUncertaintyValue, "invalid_expanded_uncertainty_value");
  assertPositive(input.coverageFactor, "invalid_coverage_factor");

  const resultFormatted = `${formatNumber(input.resultValue)} ${unit}`;
  const uncertaintyFormatted = `±${formatNumber(input.expandedUncertaintyValue)} ${unit}`;
  const coverageFactorFormatted = `k=${formatNumber(input.coverageFactor)}`;

  return {
    result: {
      value: input.resultValue,
      unit,
      formatted: resultFormatted,
    },
    expandedUncertainty: {
      value: input.expandedUncertaintyValue,
      unit,
      formatted: uncertaintyFormatted,
    },
    coverageFactor: {
      value: input.coverageFactor,
      formatted: coverageFactorFormatted,
    },
    summary: `Resultado: ${resultFormatted} | U: ${uncertaintyFormatted} | ${coverageFactorFormatted}`,
  };
}

function assertFiniteNumber(value: number, code: string) {
  if (!Number.isFinite(value)) {
    throw new Error(code);
  }
}

function assertPositiveOrZero(value: number, code: string) {
  assertFiniteNumber(value, code);
  if (value < 0) {
    throw new Error(code);
  }
}

function assertPositive(value: number, code: string) {
  assertFiniteNumber(value, code);
  if (value <= 0) {
    throw new Error(code);
  }
}

function formatNumber(value: number) {
  return Number.isInteger(value) ? String(value) : String(value);
}
