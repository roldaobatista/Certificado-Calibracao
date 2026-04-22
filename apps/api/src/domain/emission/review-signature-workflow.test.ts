import assert from "node:assert/strict";
import { test } from "node:test";

import { evaluateReviewSignatureWorkflow, type WorkflowMembershipInput } from "./review-signature-workflow.js";

const EXECUTOR: WorkflowMembershipInput = {
  userId: "tech-1",
  displayName: "Joao Executor",
  organizationId: "org-acme",
  roles: ["technician"],
  active: true,
  mfaEnabled: false,
  authorizedInstrumentTypes: ["balanca"],
  pendingAssignments: 0,
};

const REVIEWER: WorkflowMembershipInput = {
  userId: "reviewer-1",
  displayName: "Maria Revisora",
  organizationId: "org-acme",
  roles: ["technical_reviewer"],
  active: true,
  mfaEnabled: false,
  authorizedInstrumentTypes: ["balanca"],
  pendingAssignments: 1,
};

const QUALITY_MANAGER: WorkflowMembershipInput = {
  userId: "quality-1",
  displayName: "Renata Qualidade",
  organizationId: "org-acme",
  roles: ["quality_manager"],
  active: true,
  mfaEnabled: true,
  authorizedInstrumentTypes: ["balanca"],
  pendingAssignments: 0,
};

const SIGNATORY: WorkflowMembershipInput = {
  userId: "signatory-1",
  displayName: "Carlos Signatario",
  organizationId: "org-acme",
  roles: ["signatory"],
  active: true,
  mfaEnabled: true,
  authorizedInstrumentTypes: ["balanca"],
  pendingAssignments: 2,
};

test("keeps the review/signature workflow ready when executor reviewer and signatory are segregated", () => {
  const result = evaluateReviewSignatureWorkflow({
    organizationId: "org-acme",
    instrumentType: "balanca",
    stage: "in_review",
    executor: EXECUTOR,
    reviewer: REVIEWER,
    signatory: SIGNATORY,
    candidates: [EXECUTOR, REVIEWER, QUALITY_MANAGER, SIGNATORY],
  });

  assert.equal(result.status, "ready");
  assert.equal(result.reviewStep.status, "ready");
  assert.equal(result.signatureStep.status, "pending");
  assert.deepEqual(result.allowedActions, ["review_certificate", "reject_to_executor"]);
  assert.deepEqual(result.blockers, []);
});

test("fails closed when the reviewer matches the executor and suggests a valid replacement", () => {
  const result = evaluateReviewSignatureWorkflow({
    organizationId: "org-acme",
    instrumentType: "balanca",
    stage: "in_review",
    executor: EXECUTOR,
    reviewer: { ...EXECUTOR, roles: ["technician", "technical_reviewer"] },
    signatory: SIGNATORY,
    candidates: [EXECUTOR, REVIEWER, QUALITY_MANAGER, SIGNATORY],
  });

  assert.equal(result.status, "blocked");
  assert.equal(result.reviewStep.status, "blocked");
  assert.match(result.blockers.join("\n"), /revisor deve ser diferente do executor/i);
  assert.equal(result.suggestions.reviewer?.userId, "quality-1");
});

test("fails closed when the signatory has no MFA after technical approval", () => {
  const result = evaluateReviewSignatureWorkflow({
    organizationId: "org-acme",
    instrumentType: "balanca",
    stage: "approved",
    executor: EXECUTOR,
    reviewer: REVIEWER,
    signatory: { ...SIGNATORY, mfaEnabled: false },
    candidates: [EXECUTOR, REVIEWER, QUALITY_MANAGER, SIGNATORY],
  });

  assert.equal(result.status, "blocked");
  assert.equal(result.reviewStep.status, "complete");
  assert.equal(result.signatureStep.status, "blocked");
  assert.match(result.blockers.join("\n"), /MFA obrigatorio/i);
  assert.equal(result.suggestions.signatory?.userId, "signatory-1");
});

test("fails closed when an assigned actor does not belong to the active organization", () => {
  const result = evaluateReviewSignatureWorkflow({
    organizationId: "org-acme",
    instrumentType: "balanca",
    stage: "in_review",
    executor: EXECUTOR,
    reviewer: { ...REVIEWER, organizationId: "org-other" },
    signatory: SIGNATORY,
    candidates: [EXECUTOR, REVIEWER, QUALITY_MANAGER, SIGNATORY],
  });

  assert.equal(result.status, "blocked");
  assert.equal(result.checks.find((check) => check.id === "reviewer_membership")?.status, "failed");
});
