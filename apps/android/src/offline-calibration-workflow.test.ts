import assert from "node:assert/strict";
import { test } from "node:test";

import { completeMobileOfflineCalibration } from "./offline-calibration-workflow.js";

test("completes the calibration entirely on Android while offline and produces a local certificate draft", () => {
  const result = completeMobileOfflineCalibration({
    sessionId: "sess-001",
    workOrderId: "wo-001",
    organizationId: "org-acme",
    deviceId: "android-01",
    networkState: "offline",
    reservedCertificateNumber: "ACME-000126",
    measurements: [
      { parameterId: "mass-100kg", value: 100.002, unit: "kg" },
      { parameterId: "mass-200kg", value: 199.998, unit: "kg" },
    ],
    technicalReviewCompleted: true,
    certificateSignedOnDevice: true,
    equipmentId: "eq-001",
    customerId: "cust-001",
  });

  assert.equal(result.ok, true);
  assert.equal(result.reason, undefined);
  assert.equal(result.certificateDraft?.certificateNumber, "ACME-000126");
  assert.equal(result.certificateDraft?.generatedOnDevice, true);
  assert.equal(result.certificateDraft?.syncState, "pending_sync");
  assert.equal(result.certificateDraft?.measurementCount, 2);
});

test("fails closed when required offline data is missing or the final device approvals are incomplete", () => {
  const missingPayload = completeMobileOfflineCalibration({
    sessionId: "sess-002",
    workOrderId: "wo-002",
    organizationId: "org-acme",
    deviceId: "android-01",
    networkState: "offline",
    reservedCertificateNumber: "",
    measurements: [],
    technicalReviewCompleted: true,
    certificateSignedOnDevice: true,
    equipmentId: "eq-001",
    customerId: "cust-001",
  });

  assert.equal(missingPayload.ok, false);
  assert.equal(missingPayload.reason, "missing_required_data");

  const missingReview = completeMobileOfflineCalibration({
    sessionId: "sess-003",
    workOrderId: "wo-003",
    organizationId: "org-acme",
    deviceId: "android-01",
    networkState: "offline",
    reservedCertificateNumber: "ACME-000127",
    measurements: [{ parameterId: "mass-100kg", value: 100.001, unit: "kg" }],
    technicalReviewCompleted: false,
    certificateSignedOnDevice: true,
    equipmentId: "eq-001",
    customerId: "cust-001",
  });

  assert.equal(missingReview.ok, false);
  assert.equal(missingReview.reason, "technical_review_pending");

  const missingSignature = completeMobileOfflineCalibration({
    sessionId: "sess-004",
    workOrderId: "wo-004",
    organizationId: "org-acme",
    deviceId: "android-01",
    networkState: "offline",
    reservedCertificateNumber: "ACME-000128",
    measurements: [{ parameterId: "mass-100kg", value: 99.999, unit: "kg" }],
    technicalReviewCompleted: true,
    certificateSignedOnDevice: false,
    equipmentId: "eq-001",
    customerId: "cust-001",
  });

  assert.equal(missingSignature.ok, false);
  assert.equal(missingSignature.reason, "signature_pending");
});
