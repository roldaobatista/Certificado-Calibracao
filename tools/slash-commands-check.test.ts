import assert from "node:assert/strict";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { checkRegulatorySlashCommands } from "./slash-commands-check";

const REQUIRED_COMMANDS = ["spec-norm-diff", "ac-evidence", "claim-check", "tenant-fuzz", "emit-cert-dry"] as const;

function makeWorkspace() {
  const root = join(tmpdir(), `afere-slash-commands-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  mkdirSync(join(root, ".claude", "commands"), { recursive: true });
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function writeCommand(root: string, name: string, overrides: string[] = []) {
  const fields = [
    `description: ${name} command`,
    "owner: product-governance",
    "risk_level: high",
    "required_commands: [pnpm check:all]",
    ...overrides,
  ];

  writeFileSync(
    join(root, ".claude", "commands", `${name}.md`),
    [
      "---",
      ...fields,
      "---",
      "",
      `# /${name}`,
      "",
      "## Objetivo",
      "",
      "Executar gate regulatório.",
      "",
      "## Execução",
      "",
      "```bash",
      "pnpm check:all",
      "```",
      "",
      "## Evidência",
      "",
      "- Registrar saída do comando.",
      "",
      "## Escalonamento",
      "",
      "- Falha bloqueia merge e escala para `product-governance`.",
      "",
      "## Referências",
      "",
      "- `harness/STATUS.md`",
      "",
    ].join("\n"),
  );
}

function writeCompleteWorkspace(root: string) {
  for (const command of REQUIRED_COMMANDS) writeCommand(root, command);
}

test("fails closed when required regulatory slash commands are missing", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCommand(root, "claim-check");

    const result = checkRegulatorySlashCommands(root);

    assert.match(result.errors.join("\n"), /SLASH-001/);
    assert.match(result.errors.join("\n"), /spec-norm-diff\.md/);
    assert.match(result.errors.join("\n"), /ac-evidence\.md/);
  } finally {
    cleanup();
  }
});

test("fails when a command lacks standard frontmatter and required sections", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteWorkspace(root);
    writeFileSync(
      join(root, ".claude", "commands", "spec-norm-diff.md"),
      [
        "---",
        "description: incomplete",
        "owner: unknown-agent",
        "risk_level: trivial",
        "---",
        "",
        "# /spec-norm-diff",
        "",
      ].join("\n"),
    );

    const result = checkRegulatorySlashCommands(root);

    assert.match(result.errors.join("\n"), /SLASH-002/);
    assert.match(result.errors.join("\n"), /required_commands/);
    assert.match(result.errors.join("\n"), /SLASH-003/);
    assert.match(result.errors.join("\n"), /owner inválido/);
    assert.match(result.errors.join("\n"), /SLASH-004/);
    assert.match(result.errors.join("\n"), /## Execução/);
  } finally {
    cleanup();
  }
});

test("fails when a command has no executable command block", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteWorkspace(root);
    writeFileSync(
      join(root, ".claude", "commands", "tenant-fuzz.md"),
      [
        "---",
        "description: tenant fuzz",
        "owner: qa-acceptance",
        "risk_level: blocker",
        "required_commands: [pnpm test:tenancy]",
        "---",
        "",
        "# /tenant-fuzz",
        "",
        "## Objetivo",
        "",
        "Validar tenancy.",
        "",
        "## Execução",
        "",
        "Rodar o teste manualmente.",
        "",
        "## Evidência",
        "",
        "- Saída do teste.",
        "",
        "## Escalonamento",
        "",
        "- Escalar falha.",
        "",
        "## Referências",
        "",
        "- `harness/05-guardrails.md`",
        "",
      ].join("\n"),
    );

    const result = checkRegulatorySlashCommands(root);

    assert.match(result.errors.join("\n"), /SLASH-005/);
    assert.match(result.errors.join("\n"), /tenant-fuzz/);
  } finally {
    cleanup();
  }
});

test("passes for complete regulatory slash commands", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    writeCompleteWorkspace(root);

    const result = checkRegulatorySlashCommands(root);

    assert.deepEqual(result.errors, []);
    assert.equal(result.checkedCommands, 5);
  } finally {
    cleanup();
  }
});
