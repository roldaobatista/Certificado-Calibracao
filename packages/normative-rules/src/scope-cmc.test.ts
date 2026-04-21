import assert from "node:assert/strict";
import { test } from "node:test";

import { evaluateAccreditedScopeCmc } from "./scope-cmc.js";

test("allows accredited emission when type A is active in scope and U is not below CMC", () => {
  const result = evaluateAccreditedScopeCmc({
    profile: "A",
    accreditationActive: true,
    hasRegisteredScope: true,
    hasRegisteredCmc: true,
    withinAccreditedScope: true,
    expandedUncertainty: 0.6,
    declaredCmc: 0.5,
  });

  assert.equal(result.canEmitCertificate, true);
  assert.equal(result.canUseAccreditationSymbol, true);
  assert.equal(result.symbolPolicy, "allowed");
  assert.deepEqual(result.blockers, []);
  assert.deepEqual(result.warnings, []);
});

test("suppresses the accreditation symbol when the item is outside accredited scope", () => {
  const result = evaluateAccreditedScopeCmc({
    profile: "A",
    accreditationActive: true,
    hasRegisteredScope: true,
    hasRegisteredCmc: true,
    withinAccreditedScope: false,
    expandedUncertainty: 0.6,
    declaredCmc: 0.5,
  });

  assert.equal(result.canEmitCertificate, true);
  assert.equal(result.canUseAccreditationSymbol, false);
  assert.equal(result.symbolPolicy, "suppressed");
  assert.equal(result.warnings.includes("outside_accredited_scope"), true);
});

test("blocks point emission when expanded uncertainty is below the declared CMC", () => {
  const result = evaluateAccreditedScopeCmc({
    profile: "A",
    accreditationActive: true,
    hasRegisteredScope: true,
    hasRegisteredCmc: true,
    withinAccreditedScope: true,
    expandedUncertainty: 0.4,
    declaredCmc: 0.5,
  });

  assert.equal(result.canEmitCertificate, false);
  assert.equal(result.canUseAccreditationSymbol, false);
  assert.equal(result.symbolPolicy, "blocked");
  assert.deepEqual(result.blockers, ["uncertainty_below_cmc"]);
});

test("blocks type A accredited flow when scope or CMC registration is missing", () => {
  const result = evaluateAccreditedScopeCmc({
    profile: "A",
    accreditationActive: true,
    hasRegisteredScope: false,
    hasRegisteredCmc: false,
    withinAccreditedScope: true,
    expandedUncertainty: 0.6,
    declaredCmc: 0.5,
  });

  assert.equal(result.canEmitCertificate, false);
  assert.equal(result.canUseAccreditationSymbol, false);
  assert.deepEqual(result.blockers, ["missing_scope_registration", "missing_cmc_registration"]);
});
