import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { test } from "node:test";

import { load as yamlLoad } from "js-yaml";

type GovernanceRaciEntry = {
  activity: string;
  responsible: string[];
  accountable: string[];
  consulted: string[];
  informed: string[];
};

type GovernanceFile = {
  version: number;
  status: string;
  go_live_gate: string;
  owner?: {
    role: string;
    nominee_title: string;
    designation_source: string;
  };
  package_content_owner?: {
    role: string;
    source: string;
  };
  committee?: {
    cadence: string;
    members: string[];
  };
  package_repository?: {
    approved_root: string;
    manifest_path: string;
  };
  watchlist?: string[];
  budget?: {
    currency: string;
    line_items: Array<{
      id: string;
      amount_brl: number;
      cadence: string;
    }>;
  };
  raci?: GovernanceRaciEntry[];
};

const governanceFile = resolve("compliance/release-norm/pre-go-live-normative-governance.yaml");
const adrFile = resolve("adr/0031-normative-governance-owner.md");

function loadGovernanceFile(): GovernanceFile {
  return yamlLoad(readFileSync(governanceFile, "utf8")) as GovernanceFile;
}

function getRaciEntry(file: GovernanceFile, activity: string): GovernanceRaciEntry | undefined {
  return file.raci?.find((entry) => entry.activity === activity);
}

test("PRD §13.22: normative governance owner is explicitly named with RACI and budget before go-live", () => {
  assert.equal(
    existsSync(governanceFile),
    true,
    "missing compliance/release-norm/pre-go-live-normative-governance.yaml",
  );
  assert.equal(
    existsSync(adrFile),
    true,
    "missing adr/0031-normative-governance-owner.md",
  );

  const file = loadGovernanceFile();

  assert.equal(file.version, 1);
  assert.equal(file.status, "approved");
  assert.equal(file.go_live_gate, "required_before_first_production_certificate");

  assert.equal(file.owner?.role, "product-governance");
  assert.equal(file.owner?.nominee_title, "Responsavel Tecnico do Produto");
  assert.equal(file.owner?.designation_source, "adr/0009-tiebreaker-designation.md");

  assert.equal(file.package_content_owner?.role, "regulator");
  assert.equal(file.package_content_owner?.source, "adr/0004-normative-package-governance.md");

  assert.equal(file.committee?.cadence, "monthly");
  assert.deepEqual(file.committee?.members, [
    "gestor-da-qualidade-do-laboratorio-piloto",
    "metrologista-interno-do-produto",
    "product-manager",
  ]);

  assert.equal(file.package_repository?.approved_root, "compliance/normative-packages/approved/");
  assert.equal(file.package_repository?.manifest_path, "compliance/normative-packages/releases/manifest.yaml");
  assert.equal(existsSync(resolve(file.package_repository?.approved_root ?? "")), true, "missing approved package root");
  assert.equal(existsSync(resolve(file.package_repository?.manifest_path ?? "")), true, "missing package manifest");

  assert.equal(file.watchlist?.includes("portal-inmetro-dou-metrologia-legal-cgcre"), true);
  assert.equal(file.watchlist?.includes("publicacoes-ilac-p-series-g-series"), true);
  assert.equal(file.watchlist?.includes("atualizacoes-abnt"), true);
  assert.equal(file.watchlist?.includes("newsletters-doq-cgcre-nit-dicla"), true);

  assert.equal(file.budget?.currency, "BRL");
  assert.equal((file.budget?.line_items?.length ?? 0) >= 3, true, "budget must declare at least 3 approved line items");
  assert.equal(
    (file.budget?.line_items?.reduce((sum, item) => sum + item.amount_brl, 0) ?? 0) > 0,
    true,
    "budget total must be positive",
  );
  assert.equal(file.budget?.line_items?.some((item) => item.id === "watchlist-monitoring"), true);
  assert.equal(file.budget?.line_items?.some((item) => item.id === "external-specialist-review"), true);
  assert.equal(file.budget?.line_items?.some((item) => item.id === "critical-change-contingency"), true);

  const activities = [
    "monitoracao-semanal",
    "analise-de-impacto",
    "planejamento-release-norm",
    "implementacao",
    "validacao",
    "comunicacao",
  ];

  for (const activity of activities) {
    const entry = getRaciEntry(file, activity);
    assert.ok(entry, `missing RACI activity ${activity}`);
    assert.equal(entry?.accountable.includes("product-governance"), true, `${activity} must keep product-governance accountable`);
    assert.equal(entry?.responsible.length ? true : false, true, `${activity} must declare responsible roles`);
  }

  assert.equal(
    getRaciEntry(file, "monitoracao-semanal")?.responsible.includes("regulator"),
    true,
    "regulator must own weekly monitoring execution",
  );
  assert.equal(
    getRaciEntry(file, "validacao")?.consulted.includes("metrology-auditor"),
    true,
    "validation must consult metrology-auditor",
  );
  assert.equal(
    getRaciEntry(file, "validacao")?.consulted.includes("legal-counsel"),
    true,
    "validation must consult legal-counsel",
  );
  assert.equal(
    getRaciEntry(file, "comunicacao")?.informed.includes("organizacoes-clientes"),
    true,
    "communication must inform client organizations",
  );
});
