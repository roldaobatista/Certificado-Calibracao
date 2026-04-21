const UTC_ISO_TIMESTAMP = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/;

export interface SignatoryCompetenceRecord {
  instrumentType: string;
  validFromUtc: string;
  validUntilUtc: string;
}

export interface EvaluateSignatoryCompetenceInput {
  signatoryId: string;
  instrumentType: string;
  signedAtUtc: string;
  competencies: SignatoryCompetenceRecord[];
}

export interface EvaluateSignatoryCompetenceResult {
  ok: boolean;
  reason?:
    | "missing_required_data"
    | "invalid_signed_at"
    | "invalid_competence_record"
    | "no_competence_for_instrument"
    | "competence_not_current";
  matchedCompetence?: SignatoryCompetenceRecord;
}

export function evaluateSignatoryCompetence(
  input: EvaluateSignatoryCompetenceInput,
): EvaluateSignatoryCompetenceResult {
  if (
    !isNonEmptyString(input.signatoryId) ||
    !isNonEmptyString(input.instrumentType) ||
    !isNonEmptyString(input.signedAtUtc) ||
    input.competencies.length === 0
  ) {
    return { ok: false, reason: "missing_required_data" };
  }

  if (!isUtcIsoTimestamp(input.signedAtUtc)) {
    return { ok: false, reason: "invalid_signed_at" };
  }

  for (const competence of input.competencies) {
    if (
      !isNonEmptyString(competence.instrumentType) ||
      !isUtcIsoTimestamp(competence.validFromUtc) ||
      !isUtcIsoTimestamp(competence.validUntilUtc) ||
      Date.parse(competence.validFromUtc) > Date.parse(competence.validUntilUtc)
    ) {
      return { ok: false, reason: "invalid_competence_record" };
    }
  }

  const sameInstrument = input.competencies.filter(
    (competence) => competence.instrumentType === input.instrumentType,
  );

  if (sameInstrument.length === 0) {
    return { ok: false, reason: "no_competence_for_instrument" };
  }

  const signedAt = Date.parse(input.signedAtUtc);
  const matchedCompetence = sameInstrument.find((competence) => {
    const validFrom = Date.parse(competence.validFromUtc);
    const validUntil = Date.parse(competence.validUntilUtc);
    return signedAt >= validFrom && signedAt <= validUntil;
  });

  if (!matchedCompetence) {
    return { ok: false, reason: "competence_not_current" };
  }

  return {
    ok: true,
    matchedCompetence,
  };
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isUtcIsoTimestamp(value: string): boolean {
  if (!UTC_ISO_TIMESTAMP.test(value)) return false;
  return Number.isFinite(Date.parse(value));
}
