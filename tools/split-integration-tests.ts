import fs from "node:fs";
import path from "node:path";

const src = path.resolve("apps/api/src/app.test.ts");
const destDir = path.resolve("apps/api/src/tests/integration");
const content = fs.readFileSync(src, "utf-8");

const header = `import assert from "node:assert/strict";
import { test } from "node:test";

import {
  auditTrailCatalogSchema,
  authSessionSchema,
  certificatePreviewCatalogSchema,
  complaintRegistryCatalogSchema,
  customerRegistryCatalogSchema,
  emissionDryRunCatalogSchema,
  emissionWorkspaceCatalogSchema,
  managementReviewCatalogSchema,
  nonconformingWorkCatalogSchema,
  nonconformityRegistryCatalogSchema,
  offlineSyncCatalogSchema,
  equipmentRegistryCatalogSchema,
  internalAuditCatalogSchema,
  onboardingCatalogSchema,
  organizationSettingsCatalogSchema,
  portalDashboardCatalogSchema,
  portalCertificateCatalogSchema,
  portalEquipmentCatalogSchema,
  procedureRegistryCatalogSchema,
  publicCertificateCatalogSchema,
  qualityDocumentRegistryCatalogSchema,
  qualityHubCatalogSchema,
  qualityIndicatorRegistryCatalogSchema,
  riskRegisterCatalogSchema,
  reviewSignatureCatalogSchema,
  serviceOrderReviewCatalogSchema,
  selfSignupCatalogSchema,
  signatureQueueCatalogSchema,
  standardRegistryCatalogSchema,
  userDirectoryCatalogSchema,
} from "@afere/contracts";

import { buildApp } from "../../app.js";
import { createMemoryCorePersistence } from "../../domain/auth/core-persistence.js";
import { createMemoryServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import { createMemoryQualityPersistence } from "../../domain/quality/quality-persistence.js";
import { createMemoryRegistryPersistence } from "../../domain/registry/registry-persistence.js";
`;

const helpersImport = `import {
  TEST_ENV,
  createRuntimeReadinessStub,
  normalizeCookieHeader,
  createV1MemorySeed,
  createV2RegistrySeed,
  createV3CoreSeed,
  createV3ServiceOrderSeed,
  createV4CoreSeed,
  createV4RegistrySeed,
  createV4ServiceOrderSeed,
  createV5QualitySeed,
  buildMeasurementRawDataFixture,
  buildEquipmentMetrologyProfileFixture,
  buildStandardMetrologyProfileFixture,
  buildSeedEmissionAuditTrail,
} from "./helpers.js";
`;

interface Block {
  name: string;
  start: number;
  end: number;
}

const lines = content.split("\n");
const blocks: Block[] = [];
let currentBlock: Block | null = null;

for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  if (line.match(/^test\("/)) {
    if (currentBlock) {
      currentBlock.end = i;
      blocks.push(currentBlock);
    }
    const nameMatch = line.match(/^test\("([^"]+)"/);
    currentBlock = { name: nameMatch?.[1] ?? `test-${i}`, start: i, end: -1 };
  }
}
if (currentBlock) {
  currentBlock.end = lines.length;
  blocks.push(currentBlock);
}

function categorize(name: string): string {
  const n = name.toLowerCase();
  if (n.includes("healthz") || n.includes("readyz")) return "health";
  if (n.includes("catalog") || n.includes("dry-run")) return "catalogs";
  if (n.includes("session") || n.includes("authenticated tenant context")) return "auth";
  if (n.includes("rbac") || n.includes("user directory") || n.includes("onboarding")) return "auth";
  if (n.includes("persisted v2 registry")) return "registry";
  if (n.includes("admin") || n.includes("manage persisted")) return "registry-management";
  if (n.includes("service order") && !n.includes("v3") && !n.includes("v4") && !n.includes("v5")) return "service-orders";
  if (n.includes("v3") || n.includes("emission") || n.includes("review") || n.includes("uncertainty") || n.includes("blocks") || n.includes("requires justification") || n.includes("approves and emits")) return "emission-v3";
  if (n.includes("v4") || n.includes("portal") || n.includes("public qr") || n.includes("reissues")) return "portal-v4";
  if (n.includes("v5") || n.includes("quality") || n.includes("governance") || n.includes("nonconformity") || n.includes("indicator") || n.includes("management review") || n.includes("compliance profile")) return "quality-v5";
  return "catalogs";
}

const grouped = new Map<string, Block[]>();
for (const block of blocks) {
  const cat = categorize(block.name);
  if (!grouped.has(cat)) grouped.set(cat, []);
  grouped.get(cat)!.push(block);
}

for (const [cat, catBlocks] of grouped) {
  const outPath = path.join(destDir, `${cat}.test.ts`);
  const blockContents: string[] = [];
  for (const block of catBlocks) {
    const slice = lines.slice(block.start, block.end);
    blockContents.push(slice.join("\n"));
  }
  const out = header + "\n" + helpersImport + "\n" + blockContents.join("\n\n") + "\n";
  fs.writeFileSync(outPath, out, "utf-8");
  console.log(`Wrote ${outPath} (${catBlocks.length} test(s))`);
}

console.log("Done.");
