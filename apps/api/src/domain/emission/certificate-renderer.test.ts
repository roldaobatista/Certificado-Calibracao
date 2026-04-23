import assert from "node:assert/strict";
import test from "node:test";

import { resolveEmissionDryRunScenario } from "./dry-run-scenarios.js";
import {
  CERTIFICATE_PDFA_STATUS,
  CERTIFICATE_RENDERER_ID,
  buildCertificateDocumentLines,
  renderCertificateDocument,
} from "./certificate-renderer.js";

test("renders a deterministic certificate pdf from a dry-run scenario", () => {
  const scenario = resolveEmissionDryRunScenario("type-b-ready");
  const rendered = renderCertificateDocument({
    snapshotId: "profile-b-ready-01",
    label: scenario.label,
    description: scenario.description,
    input: scenario.input,
    result: scenario.result,
  });

  assert.equal(rendered.renderer, CERTIFICATE_RENDERER_ID);
  assert.equal(rendered.pdfaStatus, CERTIFICATE_PDFA_STATUS);
  assert.equal(rendered.fileName, "profile-b-ready-01.pdf");
  assert.match(rendered.bytes.toString("binary", 0, 8), /%PDF-1.4/);
  assert.match(rendered.bytes.toString("binary"), /AFERE - CERTIFICADO CANONICO DE CALIBRACAO/);
  assert.match(rendered.bytes.toString("binary"), /PDFA STATUS: pending_external_validation/);
  assert.equal(rendered.sha256.length, 64);
});

test("certificate document lines keep the fail-closed PDF/A disclaimer", () => {
  const scenario = resolveEmissionDryRunScenario("type-c-blocked");
  const lines = buildCertificateDocumentLines({
    snapshotId: "profile-c-blocked-01",
    label: scenario.label,
    description: scenario.description,
    input: scenario.input,
    result: scenario.result,
  });

  assert.equal(lines.some((line) => line.includes("BLOQUEIOS")), true);
  assert.equal(lines.some((line) => line.includes("NOTA REGULATORIA")), true);
  assert.equal(lines.some((line) => line.includes("validacao externa")), true);
});
