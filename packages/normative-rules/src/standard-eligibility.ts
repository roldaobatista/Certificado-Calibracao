export type StandardEligibilityDecision = {
  eligible: boolean;
  blockers: string[];
  warnings: string[];
};

export function evaluateStandardEligibility(input: {
  calibrationDate: string;
  hasValidCertificate: boolean;
  certificateValidUntil?: string;
  measurementValue?: number;
  applicableRange?: {
    minimum: number;
    maximum: number;
  };
}): StandardEligibilityDecision {
  const blockers: string[] = [];

  const calibrationDate = parseIsoDate(input.calibrationDate);
  if (calibrationDate === null) {
    blockers.push("invalid_calibration_date");
  }

  if (!input.hasValidCertificate) {
    blockers.push("missing_valid_certificate");
  }

  if (input.hasValidCertificate) {
    const certificateValidUntil = parseIsoDate(input.certificateValidUntil);
    if (certificateValidUntil === null) {
      blockers.push("missing_certificate_validity");
    } else if (calibrationDate !== null && certificateValidUntil.getTime() < calibrationDate.getTime()) {
      blockers.push("expired_certificate");
    }
  }

  if (input.applicableRange === undefined) {
    blockers.push("missing_applicable_range");
  } else {
    const { minimum, maximum } = input.applicableRange;
    if (!Number.isFinite(minimum) || !Number.isFinite(maximum) || minimum > maximum) {
      blockers.push("invalid_applicable_range");
    } else if (
      typeof input.measurementValue !== "number" ||
      !Number.isFinite(input.measurementValue)
    ) {
      blockers.push("missing_measurement_value");
    } else if (input.measurementValue < minimum || input.measurementValue > maximum) {
      blockers.push("standard_out_of_applicable_range");
    }
  }

  return {
    eligible: blockers.length === 0,
    blockers,
    warnings: [],
  };
}

function parseIsoDate(value: string | undefined) {
  if (typeof value !== "string" || value.trim().length === 0) {
    return null;
  }

  const parsed = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}
