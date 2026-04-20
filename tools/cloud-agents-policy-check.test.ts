import assert from "node:assert/strict";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { checkCloudAgentsPolicy, evaluateCloudAgentPullRequest } from "./cloud-agents-policy-check";

function makeWorkspace() {
  const root = join(tmpdir(), `afere-cloud-agents-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(join(root, "compliance", "cloud-agents", "attestations"), { recursive: true });
  mkdirSync(join(root, "compliance", "incidents"), { recursive: true });
  mkdirSync(join(root, "harness"), { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function writeCompletePolicy(root: string) {
  writeFileSync(
    join(root, "harness", "09-cloud-agents-policy.md"),
    [
      "# 09 - Politica de Tier 3 (cloud agents)",
      "",
      "SLSA Build Level 2+",
      "Sigstore (cosign)",
      "GitHub Artifact Attestations",
      "Fallback: sem attestation, cloud agent proibido.",
      "",
    ].join("\n"),
  );
  writeFileSync(
    join(root, "compliance", "cloud-agents-policy.md"),
    [
      "# Politica de Tier 3",
      "",
      "Allowlist explicita, blocklist dura, fixtures sinteticas e provenance attestation obrigatoria.",
      "",
    ].join("\n"),
  );
  writeFileSync(
    join(root, "compliance", "cloud-agents-log.md"),
    "# Cloud agents log\n\nRegistro append-only de attestations verificadas.\n",
  );
  writeFileSync(
    join(root, "compliance", "incidents", "cloud-agent-attestation-failure-template.md"),
    [
      "---",
      "incident_type: cloud-agent-attestation-failure",
      "status: open",
      "owner: product-governance",
      "---",
      "",
      "## Escopo",
      "",
      "## Evidencia",
      "",
      "## Correcao",
      "",
    ].join("\n"),
  );
  writeFileSync(
    join(root, "compliance", "cloud-agents", "attestations", "_template.yaml"),
    [
      "schema_version: 1",
      "mechanism: github-artifact-attestations",
      "subject_commit: <commit-sha>",
      "issuer: https://token.actions.githubusercontent.com",
      "identity: cloud-agent@example.afere.test",
      "predicate_type: https://slsa.dev/provenance/v1",
      "verified_at: 2026-04-20T12:00:00-04:00",
      "verifier_command: gh attestation verify --repo roldaobatista/Certificado-Calibracao <artifact>",
      "",
    ].join("\n"),
  );
  writeFileSync(
    join(root, "compliance", "cloud-agents", "policy.yaml"),
    [
      "version: 1",
      "source: harness/09-cloud-agents-policy.md",
      "status: enforced",
      "allowlist:",
      "  - apps/web/ui/components/**",
      "  - apps/portal/ui/**",
      "  - docs/**",
      "  - evals/fixtures/synthetic/**",
      "  - tests/unit/**",
      "blocklist:",
      "  - apps/api/**",
      "  - apps/android/**",
      "  - packages/engine-uncertainty/**",
      "  - packages/normative-rules/**",
      "  - packages/db/**",
      "  - packages/audit-log/**",
      "  - compliance/**",
      "  - specs/**",
      "  - .claude/agents/**",
      "  - infra/**",
      "provenance:",
      "  require_verified_attestation: true",
      "  deny_without_attestation: true",
      "  accepted_mechanisms:",
      "    - slsa-build-level-2-plus",
      "    - sigstore-cosign",
      "    - github-artifact-attestations",
      "  allowed_issuers:",
      "    - https://token.actions.githubusercontent.com",
      "  required_verifier_commands:",
      "    - gh attestation verify",
      "    - cosign verify-blob",
      "fixture_scanner:",
      "  synthetic_only: true",
      "  allowed_email_domain: example.afere.test",
      "  synthetic_name_prefix: TEST_",
      "incident:",
      "  failure_template: compliance/incidents/cloud-agent-attestation-failure-template.md",
      "  audit_log: compliance/cloud-agents-log.md",
      "",
    ].join("\n"),
  );
}

function writeValidAttestation(root: string, commitSha = "abc123") {
  const path = join(root, "attestation.yaml");
  writeFileSync(
    path,
    [
      "schema_version: 1",
      "mechanism: github-artifact-attestations",
      `subject_commit: ${commitSha}`,
      "issuer: https://token.actions.githubusercontent.com",
      "identity: cloud-agent[bot]",
      "predicate_type: https://slsa.dev/provenance/v1",
      "verified_at: 2026-04-20T12:00:00-04:00",
      "verifier_command: gh attestation verify --repo roldaobatista/Certificado-Calibracao abc123",
      "",
    ].join("\n"),
  );
  return path;
}

test("fails when canonical cloud agent policy artifacts are missing", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const result = checkCloudAgentsPolicy(root);

    assert.match(result.errors.join("\n"), /CLOUD-001/);
    assert.match(result.errors.join("\n"), /compliance\/cloud-agents\/policy\.yaml/);
    assert.match(result.errors.join("\n"), /cloud-agents-log\.md/);
  } finally {
    cleanup();
  }
});

test("fails when policy does not require strong provenance mechanisms", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompletePolicy(root);
    writeFileSync(
      join(root, "compliance", "cloud-agents", "policy.yaml"),
      [
        "version: 1",
        "source: harness/09-cloud-agents-policy.md",
        "status: draft",
        "allowlist: [docs/**]",
        "blocklist: [apps/api/**]",
        "provenance:",
        "  require_verified_attestation: false",
        "  deny_without_attestation: false",
        "  accepted_mechanisms:",
        "    - user-agent",
        "",
      ].join("\n"),
    );

    const result = checkCloudAgentsPolicy(root);

    assert.match(result.errors.join("\n"), /CLOUD-002/);
    assert.match(result.errors.join("\n"), /slsa-build-level-2-plus/);
    assert.match(result.errors.join("\n"), /sigstore-cosign/);
  } finally {
    cleanup();
  }
});

test("fails closed for cloud-agent branches without attestation", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompletePolicy(root);

    const result = evaluateCloudAgentPullRequest(root, {
      branchName: "cloud-agent/ui-copy",
      changedFiles: ["docs/cloud-agent-notes.md"],
      commitSha: "abc123",
    });

    assert.match(result.errors.join("\n"), /CLOUD-PR-002/);
    assert.match(result.errors.join("\n"), /attestation/);
  } finally {
    cleanup();
  }
});

test("blocks cloud-agent branches touching blocklisted paths", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompletePolicy(root);
    const attestationPath = writeValidAttestation(root);

    const result = evaluateCloudAgentPullRequest(root, {
      branchName: "cloud-agent/api-refactor",
      changedFiles: ["apps/api/src/domain/emission/service.ts"],
      commitSha: "abc123",
      attestationPath,
    });

    assert.match(result.errors.join("\n"), /CLOUD-PR-001/);
    assert.match(result.errors.join("\n"), /apps\/api/);
  } finally {
    cleanup();
  }
});

test("passes allowlisted cloud-agent branches with verified attestation manifest", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompletePolicy(root);
    const attestationPath = writeValidAttestation(root);

    const result = evaluateCloudAgentPullRequest(root, {
      branchName: "cloud-agent/ui-copy",
      changedFiles: ["docs/cloud-agent-notes.md", "evals/fixtures/synthetic/customers.yaml"],
      commitSha: "abc123",
      attestationPath,
    });

    assert.deepEqual(result.errors, []);
    assert.equal(result.checkedAllowedPaths, 2);
    assert.equal(result.attestationVerified, true);
  } finally {
    cleanup();
  }
});
