import assert from "node:assert/strict";
import { test } from "node:test";

import { evaluateSignatoryCompetence } from "./signatory-competence.js";

test("allows signature when the signatory has active competence for the instrument type", () => {
  const result = evaluateSignatoryCompetence({
    signatoryId: "sig-1",
    instrumentType: "balanca-ipna",
    signedAtUtc: "2026-04-21T14:00:00Z",
    competencies: [
      {
        instrumentType: "balanca-ipna",
        validFromUtc: "2026-01-01T00:00:00Z",
        validUntilUtc: "2026-12-31T23:59:59Z",
      },
    ],
  });

  assert.equal(result.ok, true);
  assert.equal(result.reason, undefined);
});

test("blocks signature when competence is missing for the instrument or no longer current", () => {
  const wrongInstrument = evaluateSignatoryCompetence({
    signatoryId: "sig-1",
    instrumentType: "termometro",
    signedAtUtc: "2026-04-21T14:00:00Z",
    competencies: [
      {
        instrumentType: "balanca-ipna",
        validFromUtc: "2026-01-01T00:00:00Z",
        validUntilUtc: "2026-12-31T23:59:59Z",
      },
    ],
  });

  assert.equal(wrongInstrument.ok, false);
  assert.equal(wrongInstrument.reason, "no_competence_for_instrument");

  const expired = evaluateSignatoryCompetence({
    signatoryId: "sig-1",
    instrumentType: "balanca-ipna",
    signedAtUtc: "2026-04-21T14:00:00Z",
    competencies: [
      {
        instrumentType: "balanca-ipna",
        validFromUtc: "2025-01-01T00:00:00Z",
        validUntilUtc: "2025-12-31T23:59:59Z",
      },
    ],
  });

  assert.equal(expired.ok, false);
  assert.equal(expired.reason, "competence_not_current");
});

test("fails closed when required data or competence windows are invalid", () => {
  const missingData = evaluateSignatoryCompetence({
    signatoryId: "",
    instrumentType: "balanca-ipna",
    signedAtUtc: "2026-04-21T14:00:00Z",
    competencies: [],
  });

  assert.equal(missingData.ok, false);
  assert.equal(missingData.reason, "missing_required_data");

  const invalidRecord = evaluateSignatoryCompetence({
    signatoryId: "sig-1",
    instrumentType: "balanca-ipna",
    signedAtUtc: "2026-04-21T14:00:00Z",
    competencies: [
      {
        instrumentType: "balanca-ipna",
        validFromUtc: "2026-12-31T23:59:59Z",
        validUntilUtc: "2026-01-01T00:00:00Z",
      },
    ],
  });

  assert.equal(invalidRecord.ok, false);
  assert.equal(invalidRecord.reason, "invalid_competence_record");
});
