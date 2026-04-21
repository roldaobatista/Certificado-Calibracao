const CERTIFICATE_NUMBER_PATTERN = /^([A-Z0-9]{2,12})-(\d{6})$/;
const ORGANIZATION_CODE_PATTERN = /^[A-Z0-9]{2,12}$/;

export interface IssuedCertificateNumber {
  organizationId: string;
  certificateNumber: string;
}

export interface ReserveSequentialCertificateNumberInput {
  organizationId: string;
  organizationCode: string;
  issuedNumbers: IssuedCertificateNumber[];
}

export interface ReserveSequentialCertificateNumberResult {
  ok: boolean;
  nextSequence?: number;
  certificateNumber?: string;
  errors: string[];
}

export function reserveSequentialCertificateNumber(
  input: ReserveSequentialCertificateNumberInput,
): ReserveSequentialCertificateNumberResult {
  const errors = new Set<string>();

  if (!isNonEmptyString(input.organizationId)) errors.add("missing_organization_id");
  if (!isNonEmptyString(input.organizationCode)) {
    errors.add("missing_organization_code");
  } else if (!ORGANIZATION_CODE_PATTERN.test(input.organizationCode)) {
    errors.add("invalid_organization_code");
  }

  const seenNumbers = new Map<string, string>();
  let highestSequence = 0;

  for (const issued of input.issuedNumbers) {
    if (!isNonEmptyString(issued.organizationId)) {
      errors.add("invalid_issued_number_owner");
      continue;
    }

    const match = issued.certificateNumber.match(CERTIFICATE_NUMBER_PATTERN);
    if (!match) {
      errors.add("invalid_issued_number_format");
      continue;
    }

    const existingOwner = seenNumbers.get(issued.certificateNumber);
    if (existingOwner && existingOwner !== issued.organizationId) {
      errors.add("existing_number_collision");
    } else {
      seenNumbers.set(issued.certificateNumber, issued.organizationId);
    }

    if (issued.organizationId !== input.organizationId) continue;

    const [, prefix, sequenceText] = match;
    if (prefix !== input.organizationCode) {
      errors.add("organization_prefix_mismatch");
      continue;
    }

    highestSequence = Math.max(highestSequence, Number(sequenceText));
  }

  if (errors.size > 0) {
    return {
      ok: false,
      errors: [...errors],
    };
  }

  const nextSequence = highestSequence + 1;
  const certificateNumber = `${input.organizationCode}-${String(nextSequence).padStart(6, "0")}`;

  if (seenNumbers.has(certificateNumber)) {
    return {
      ok: false,
      errors: ["next_number_already_allocated"],
    };
  }

  return {
    ok: true,
    nextSequence,
    certificateNumber,
    errors: [],
  };
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}
