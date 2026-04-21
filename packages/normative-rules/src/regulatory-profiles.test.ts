import assert from "node:assert/strict";
import { test } from "node:test";

import { resolveRegulatoryPdfPolicy, validateRegulatoryFreeText } from "./regulatory-profiles.js";

test("selects template-a/b/c and enforces profile-specific symbol policy", () => {
  const typeAWithinScope = resolveRegulatoryPdfPolicy({
    profile: "A",
    withinAccreditedScope: true,
  });
  assert.equal(typeAWithinScope.templateId, "template-a");
  assert.equal(typeAWithinScope.symbolPolicy, "allowed");
  assert.deepEqual(typeAWithinScope.warnings, []);

  const typeAOutOfScope = resolveRegulatoryPdfPolicy({
    profile: "A",
    withinAccreditedScope: false,
  });
  assert.equal(typeAOutOfScope.templateId, "template-a");
  assert.equal(typeAOutOfScope.symbolPolicy, "suppressed");
  assert.equal(typeAOutOfScope.warnings.includes("outside_accredited_scope"), true);

  const typeB = resolveRegulatoryPdfPolicy({ profile: "B" });
  assert.equal(typeB.templateId, "template-b");
  assert.equal(typeB.symbolPolicy, "blocked");
  assert.equal(typeB.allowedStandardSources.includes("RBC"), true);
  assert.equal(typeB.allowedStandardSources.includes("INM"), true);
  assert.deepEqual(validateRegulatoryFreeText("B", "Padroes calibrados por laboratorio RBC acreditado"), []);

  const typeC = resolveRegulatoryPdfPolicy({ profile: "C" });
  assert.equal(typeC.templateId, "template-c");
  assert.equal(typeC.symbolPolicy, "blocked");
  assert.deepEqual(typeC.forbiddenFreeTextTerms, ["RBC", "Cgcre"]);
  assert.deepEqual(
    validateRegulatoryFreeText("C", "Certificado emitido conforme RBC e Cgcre"),
    ["forbidden_term:RBC", "forbidden_term:Cgcre"],
  );
});
