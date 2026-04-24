import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { test } from "node:test";

test("starts Postgres before running check:all because tenancy is part of the main gate", () => {
  const workflow = readFileSync(resolve(process.cwd(), ".github/workflows/required-gates.yml"), "utf8");

  const structuralGate = workflow.indexOf("name: Run structural gates");
  const startPostgres = workflow.indexOf("name: Start Postgres for tenancy gates");

  assert.notEqual(startPostgres, -1);
  assert.notEqual(structuralGate, -1);
  assert.ok(
    startPostgres < structuralGate,
    "required-gates.yml deve subir Postgres antes de rodar pnpm check:all, porque check:all inclui test:tenancy.",
  );
});
