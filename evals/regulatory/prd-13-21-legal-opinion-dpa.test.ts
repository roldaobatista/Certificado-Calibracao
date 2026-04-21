import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { test } from "node:test";

import { load as yamlLoad } from "js-yaml";

type LegalBundle = {
  version: number;
  status: string;
  reviewed_by_role: string;
  reviewed_by_qualification: string;
  review_date: string;
  formal_opinion_path: string;
  dpa_template_path: string;
  controller_processor_matrix_path: string;
  legal_sources: string[];
  subprocessors: string[];
};

type MarkdownDoc = {
  frontmatter: Record<string, unknown>;
  body: string;
};

const bundlePath = resolve("compliance/legal-opinions/prd-13-21-legal-bundle.yaml");

function readYamlFile<T>(filePath: string): T {
  return yamlLoad(readFileSync(filePath, "utf8")) as T;
}

function parseMarkdownDoc(filePath: string): MarkdownDoc {
  const content = readFileSync(filePath, "utf8");
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  assert.ok(match, `missing YAML frontmatter in ${filePath}`);

  return {
    frontmatter: yamlLoad(match[1]) as Record<string, unknown>,
    body: match[2],
  };
}

test("PRD §13.21: legal opinion bundle includes formal signature opinion, DPA draft, and LGPD matrix reviewed by legal counsel", () => {
  assert.equal(existsSync(bundlePath), true, "missing compliance/legal-opinions/prd-13-21-legal-bundle.yaml");

  const bundle = readYamlFile<LegalBundle>(bundlePath);
  assert.equal(bundle.version, 1);
  assert.equal(bundle.status, "approved");
  assert.equal(bundle.reviewed_by_role, "legal-counsel");
  assert.equal(bundle.reviewed_by_qualification, "advogado-lgpd");
  assert.match(bundle.review_date, /^2026-04-21/);
  assert.equal(bundle.legal_sources.includes("mp-2200-2-art-10-par-2"), true);
  assert.equal(bundle.legal_sources.includes("lei-14063-art-4"), true);
  assert.equal(bundle.legal_sources.includes("lgpd-art-7-e-art-18"), true);
  assert.deepEqual(bundle.subprocessors, [
    "hostinger",
    "backblaze-b2",
    "aws-kms-sa-east-1",
    "grafana-cloud",
    "axiom",
  ]);

  const formalOpinionPath = resolve(bundle.formal_opinion_path);
  const dpaTemplatePath = resolve(bundle.dpa_template_path);
  const matrixPath = resolve(bundle.controller_processor_matrix_path);

  assert.equal(existsSync(formalOpinionPath), true, "missing formal legal opinion");
  assert.equal(existsSync(dpaTemplatePath), true, "missing DPA template");
  assert.equal(existsSync(matrixPath), true, "missing controller/processor matrix");

  const formalOpinion = parseMarkdownDoc(formalOpinionPath);
  assert.equal(formalOpinion.frontmatter.status, "approved");
  assert.equal(formalOpinion.frontmatter.owner, "legal-counsel");
  assert.equal(formalOpinion.frontmatter.subject, "assinatura-eletronica-auditavel");
  assert.match(formalOpinion.body, /MP 2\.200-2\/2001/i);
  assert.match(formalOpinion.body, /art\. 10, § 2º/i);
  assert.match(formalOpinion.body, /Lei nº 14\.063\/2020/i);
  assert.match(formalOpinion.body, /não exige ICP-Brasil para o MVP/i);
  assert.match(formalOpinion.body, /integridade, autoria e trilha de auditoria/i);

  const dpaTemplate = parseMarkdownDoc(dpaTemplatePath);
  assert.equal(dpaTemplate.frontmatter.status, "approved_template");
  assert.equal(dpaTemplate.frontmatter.owner, "legal-counsel");
  assert.equal(dpaTemplate.frontmatter.reviewed_by_role, "legal-counsel");
  assert.match(dpaTemplate.body, /Controlador/i);
  assert.match(dpaTemplate.body, /Operador/i);
  assert.match(dpaTemplate.body, /Suboperadores/i);
  assert.match(dpaTemplate.body, /Instruções documentadas/i);
  assert.match(dpaTemplate.body, /Direitos dos titulares/i);

  const matrix = parseMarkdownDoc(matrixPath);
  assert.equal(matrix.frontmatter.status, "approved");
  assert.equal(matrix.frontmatter.owner, "lgpd-security");
  assert.equal(matrix.frontmatter.reviewed_by_role, "legal-counsel");
  assert.match(matrix.body, /Usuários da plataforma/i);
  assert.match(matrix.body, /Clientes finais do laboratório/i);
  assert.match(matrix.body, /Leituras, evidências, certificados/i);
  assert.match(matrix.body, /Audit logs/i);
  assert.match(matrix.body, /Biometria Android/i);
});
