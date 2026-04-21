import assert from "node:assert/strict";
import { test } from "node:test";

import { evaluateStandardEligibility } from "./standard-eligibility.js";

test("allows a standard with a valid certificate and an applicable range", () => {
  const result = evaluateStandardEligibility({
    calibrationDate: "2026-04-21",
    hasValidCertificate: true,
    certificateValidUntil: "2026-12-31",
    measurementValue: 5,
    applicableRange: {
      minimum: 0,
      maximum: 10,
    },
  });

  assert.equal(result.eligible, true);
  assert.deepEqual(result.blockers, []);
});

test("blocks a standard when the certificate is missing or expired", () => {
  const missingCertificate = evaluateStandardEligibility({
    calibrationDate: "2026-04-21",
    hasValidCertificate: false,
    measurementValue: 5,
    applicableRange: {
      minimum: 0,
      maximum: 10,
    },
  });
  assert.equal(missingCertificate.eligible, false);
  assert.deepEqual(missingCertificate.blockers, ["missing_valid_certificate"]);

  const expiredCertificate = evaluateStandardEligibility({
    calibrationDate: "2026-04-21",
    hasValidCertificate: true,
    certificateValidUntil: "2026-04-20",
    measurementValue: 5,
    applicableRange: {
      minimum: 0,
      maximum: 10,
    },
  });
  assert.equal(expiredCertificate.eligible, false);
  assert.deepEqual(expiredCertificate.blockers, ["expired_certificate"]);
});

test("blocks a standard outside the applicable range and fails closed without minimum data", () => {
  const outsideRange = evaluateStandardEligibility({
    calibrationDate: "2026-04-21",
    hasValidCertificate: true,
    certificateValidUntil: "2026-12-31",
    measurementValue: 15,
    applicableRange: {
      minimum: 0,
      maximum: 10,
    },
  });
  assert.equal(outsideRange.eligible, false);
  assert.deepEqual(outsideRange.blockers, ["standard_out_of_applicable_range"]);

  const missingRange = evaluateStandardEligibility({
    calibrationDate: "2026-04-21",
    hasValidCertificate: true,
    certificateValidUntil: "2026-12-31",
    measurementValue: 5,
  });
  assert.equal(missingRange.eligible, false);
  assert.deepEqual(missingRange.blockers, ["missing_applicable_range"]);
});
