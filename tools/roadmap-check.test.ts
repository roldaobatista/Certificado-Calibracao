import assert from "node:assert/strict";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { checkRoadmap } from "./roadmap-check";

const SLICE_IDS = ["V1", "V2", "V3", "V4", "V5"] as const;

function makeWorkspace() {
  const root = join(tmpdir(), `afere-roadmap-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(join(root, "compliance", "roadmap"), { recursive: true });
  mkdirSync(join(root, "harness"), { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function writeHarnessRoadmap(root: string) {
  writeFileSync(
    join(root, "harness", "10-roadmap.md"),
    [
      "# 10 — Roadmap por fatias verticais auditáveis",
      "",
      "> **P1-4**: sequência de fatias verticais com gate regulatório de saída.",
      "",
      ...SLICE_IDS.flatMap((id) => [`### ${id} — Fatia ${id}`, "", "**Gate de saída**", "", "- Gate obrigatório.", ""]),
    ].join("\n"),
  );
}

function writeReadme(root: string) {
  writeFileSync(
    join(root, "compliance", "roadmap", "README.md"),
    [
      "# Roadmap",
      "",
      "Fonte canônica executável do roadmap V1-V5.",
      "",
      "Editar `v1-v5.yaml` e rodar `pnpm roadmap-check`.",
      "",
    ].join("\n"),
  );
}

function writeCompleteRoadmap(root: string) {
  writeReadme(root);
  writeHarnessRoadmap(root);
  writeFileSync(
    join(root, "compliance", "roadmap", "v1-v5.yaml"),
    [
      "version: 1",
      "source: harness/10-roadmap.md",
      "policy:",
      "  no_slice_starts_without_previous_gate: true",
      "  release_norm_required: true",
      "  validation_dossier_required: true",
      "  normative_package_required: true",
      "slices:",
      "  - id: V1",
      "    epic_id: EPIC-V1-EMISSAO-CONTROLADA",
      "    title: Emissão Tipo B ou C em ambiente controlado",
      "    depends_on: []",
      "    estimated_duration_weeks: '6-8'",
      "    release_norm_path: compliance/release-norm/v1.md",
      "    validation_dossier_path: compliance/validation-dossier/releases/v1.md",
      "    primary_agents: [backend-api, web-ui, db-schema, product-governance]",
      "    linked_requirements: [REQ-PRD-13-03-CERTIFICATE-MEASUREMENT-DECLARATIONS]",
      "    scope:",
      "      - Emissão online Tipo B/C",
      "      - Auth, RBAC básico, assinatura, QR e audit log",
      "    exit_gates:",
      "      - AC PRD §13 aplicáveis ao escopo Tipo B/C verdes",
      "      - Dossiê V1 fechado",
      "      - Release-norm V1 aprovado",
      "      - Pacote normativo v1.0.0 assinado",
      "  - id: V2",
      "    epic_id: EPIC-V2-SYNC-OFFLINE",
      "    title: Sync offline-first robusto",
      "    depends_on: [V1]",
      "    estimated_duration_weeks: '4-6'",
      "    release_norm_path: compliance/release-norm/v2.md",
      "    validation_dossier_path: compliance/validation-dossier/releases/v2.md",
      "    primary_agents: [android, backend-api, qa-acceptance]",
      "    linked_requirements: [REQ-PRD-13-07-ANDROID-SYNC-IDEMPOTENCY]",
      "    scope:",
      "      - Android em campo 100% offline",
      "      - Simulador determinístico C1-C8",
      "    exit_gates:",
      "      - Matriz de conflitos 100% coberta",
      "      - Seed weekly sem falha",
      "      - Dossiê V2 com trace de cada cenário",
      "  - id: V3",
      "    epic_id: EPIC-V3-TIPO-A",
      "    title: Tipo A acreditado com escopo CMC e símbolo Cgcre/RBC",
      "    depends_on: [V2]",
      "    estimated_duration_weeks: '6-8'",
      "    release_norm_path: compliance/release-norm/v3.md",
      "    validation_dossier_path: compliance/validation-dossier/releases/v3.md",
      "    primary_agents: [regulator, backend-api, web-ui, legal-counsel]",
      "    linked_requirements: [REQ-PRD-13-10-SCOPE-CMC-BLOCK]",
      "    scope:",
      "      - Perfil A habilitado",
      "      - Bloqueio de selo em Tipo B/C",
      "    exit_gates:",
      "      - Testes anti-deriva do selo Cgcre/RBC",
      "      - Regulator aprova escopo/CMC",
      "      - Parecer jurídico datado",
      "  - id: V4",
      "    epic_id: EPIC-V4-REEMISSAO",
      "    title: Reemissão controlada",
      "    depends_on: [V3]",
      "    estimated_duration_weeks: '4'",
      "    release_norm_path: compliance/release-norm/v4.md",
      "    validation_dossier_path: compliance/validation-dossier/releases/v4.md",
      "    primary_agents: [backend-api, db-schema, lgpd-security]",
      "    linked_requirements: [REQ-PRD-13-16-CONTROLLED-REISSUE]",
      "    scope:",
      "      - Reemissão com justificativa",
      "      - Hash-chain preservada",
      "    exit_gates:",
      "      - Certificado original imutável",
      "      - QR funcional para certificado antigo",
      "      - Fuzz cross-tenant verde",
      "  - id: V5",
      "    epic_id: EPIC-V5-QUALIDADE",
      "    title: Módulo Qualidade completo",
      "    depends_on: [V4]",
      "    estimated_duration_weeks: '6-8'",
      "    release_norm_path: compliance/release-norm/v5.md",
      "    validation_dossier_path: compliance/validation-dossier/releases/v5.md",
      "    primary_agents: [product-governance, metrology-auditor, qa-acceptance]",
      "    linked_requirements: []",
      "    scope:",
      "      - Não-conformidades, competências e auditorias internas",
      "      - Indicadores e análise crítica",
      "    exit_gates:",
      "      - Auditoria interna dry-run executada",
      "      - Relatório em compliance/release-norm/v5-dry-run.md",
      "      - Auditoria simulada ISO 17025 verde",
    ].join("\n"),
  );
}

test("fails when the canonical vertical roadmap artifacts are missing", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const result = checkRoadmap(root);

    assert.match(result.errors.join("\n"), /ROADMAP-001/);
    assert.match(result.errors.join("\n"), /compliance\/roadmap\/README\.md/);
    assert.match(result.errors.join("\n"), /compliance\/roadmap\/v1-v5\.yaml/);
    assert.match(result.errors.join("\n"), /harness\/10-roadmap\.md/);
  } finally {
    cleanup();
  }
});

test("fails when slices are not V1-V5 in strict dependency order", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteRoadmap(root);
    writeFileSync(
      join(root, "compliance", "roadmap", "v1-v5.yaml"),
      [
        "version: 1",
        "source: harness/10-roadmap.md",
        "policy:",
        "  no_slice_starts_without_previous_gate: true",
        "  release_norm_required: true",
        "  validation_dossier_required: true",
        "  normative_package_required: true",
        "slices:",
        "  - id: V1",
        "    epic_id: EPIC-V1-EMISSAO-CONTROLADA",
        "    title: Emissão",
        "    depends_on: []",
        "    estimated_duration_weeks: '6-8'",
        "    release_norm_path: compliance/release-norm/v1.md",
        "    validation_dossier_path: compliance/validation-dossier/releases/v1.md",
        "    primary_agents: [backend-api]",
        "    linked_requirements: [REQ-PRD-13-03-CERTIFICATE-MEASUREMENT-DECLARATIONS]",
        "    scope: [online]",
        "    exit_gates: [gate]",
        "  - id: V3",
        "    epic_id: EPIC-V3-TIPO-A",
        "    title: Tipo A",
        "    depends_on: [V1]",
        "    estimated_duration_weeks: '6-8'",
        "    release_norm_path: compliance/release-norm/v3.md",
        "    validation_dossier_path: compliance/validation-dossier/releases/v3.md",
        "    primary_agents: [regulator]",
        "    linked_requirements: [REQ-PRD-13-10-SCOPE-CMC-BLOCK]",
        "    scope: [acreditado]",
        "    exit_gates: [gate]",
      ].join("\n"),
    );

    const result = checkRoadmap(root);

    assert.match(result.errors.join("\n"), /ROADMAP-003/);
    assert.match(result.errors.join("\n"), /V2/);
  } finally {
    cleanup();
  }
});

test("fails when a slice omits epic mapping metadata", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteRoadmap(root);
    writeFileSync(
      join(root, "compliance", "roadmap", "v1-v5.yaml"),
      [
        "version: 1",
        "source: harness/10-roadmap.md",
        "policy:",
        "  no_slice_starts_without_previous_gate: true",
        "  release_norm_required: true",
        "  validation_dossier_required: true",
        "  normative_package_required: true",
        "slices:",
        "  - id: V1",
        "    title: Emissão Tipo B ou C em ambiente controlado",
        "    depends_on: []",
        "    estimated_duration_weeks: '6-8'",
        "    release_norm_path: compliance/release-norm/v1.md",
        "    validation_dossier_path: compliance/validation-dossier/releases/v1.md",
        "    primary_agents: [backend-api, web-ui, db-schema, product-governance]",
        "    scope:",
        "      - Emissão online Tipo B/C",
        "      - Auth, RBAC básico, assinatura, QR e audit log",
        "    exit_gates:",
        "      - AC PRD §13 aplicáveis ao escopo Tipo B/C verdes",
        "      - Dossiê V1 fechado",
        "      - Release-norm V1 aprovado",
        "      - Pacote normativo v1.0.0 assinado",
      ].join('\n'),
    );

    const result = checkRoadmap(root);

    assert.match(result.errors.join("\n"), /ROADMAP-004/);
    assert.match(result.errors.join("\n"), /epic_id/);
    assert.match(result.errors.join("\n"), /linked_requirements/);
  } finally {
    cleanup();
  }
});

test("fails when a slice lacks mandatory release gates", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteRoadmap(root);
    const path = join(root, "compliance", "roadmap", "v1-v5.yaml");
    const text = "version: 1\nsource: harness/10-roadmap.md\npolicy: {}\nslices: []\n";
    writeFileSync(path, text);

    const result = checkRoadmap(root);

    assert.match(result.errors.join("\n"), /ROADMAP-002/);
    assert.match(result.errors.join("\n"), /no_slice_starts_without_previous_gate/);
    assert.match(result.errors.join("\n"), /release_norm_required/);
  } finally {
    cleanup();
  }
});

test("passes for a complete V1-V5 vertical roadmap", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteRoadmap(root);

    const result = checkRoadmap(root);

    assert.deepEqual(result.errors, []);
    assert.equal(result.checkedSlices, 5);
  } finally {
    cleanup();
  }
});
