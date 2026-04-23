import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  SNAPSHOTS_PER_PROFILE,
  listCanonicalCertificateSnapshots,
} from "./certificate-snapshot-catalog.js";

type SnapshotWriteTarget = "current" | "baseline" | "both";

type SnapshotSyncOptions = {
  root?: string;
  target: SnapshotWriteTarget;
  updateManifest: boolean;
};

type GeneratedSnapshotFile = {
  id: string;
  profile: string;
  baselinePath: string;
  currentPath: string;
  sha256: string;
};

export function syncCertificateSnapshots(options: SnapshotSyncOptions): GeneratedSnapshotFile[] {
  const root = options.root ?? process.cwd();
  const snapshots = listCanonicalCertificateSnapshots();
  const snapshotsRoot = resolve(root, "compliance", "validation-dossier", "snapshots");
  const baselineDir = resolve(snapshotsRoot, "baseline");
  const currentDir = resolve(snapshotsRoot, "current");

  if (options.target === "baseline" || options.target === "both") {
    resetDirectory(baselineDir);
  }
  if (options.target === "current" || options.target === "both") {
    resetDirectory(currentDir);
  }

  for (const snapshot of snapshots) {
    if (options.target === "baseline" || options.target === "both") {
      writeFileSync(resolve(root, snapshot.baselinePath), snapshot.bytes);
    }
    if (options.target === "current" || options.target === "both") {
      writeFileSync(resolve(root, snapshot.currentPath), snapshot.bytes);
    }
  }

  if (options.updateManifest) {
    const manifestPath = resolve(snapshotsRoot, "manifest.yaml");
    writeFileSync(manifestPath, renderSnapshotManifest(snapshots));
  }

  return snapshots.map((snapshot) => ({
    id: snapshot.id,
    profile: snapshot.profile,
    baselinePath: snapshot.baselinePath,
    currentPath: snapshot.currentPath,
    sha256: snapshot.sha256,
  }));
}

export function renderSnapshotManifest(
  snapshots = listCanonicalCertificateSnapshots(),
): string {
  const lines = [
    "version: 1",
    "source: harness/05-guardrails.md",
    "policy:",
    "  profiles_required: [A, B, C]",
    `  snapshots_per_profile: ${SNAPSHOTS_PER_PROFILE}`,
    "  fail_on_diff: true",
    "  approval_required_for_baseline_update: [regulator, product-governance]",
    "snapshots:",
  ];

  for (const snapshot of snapshots) {
    lines.push(`  - id: ${snapshot.id}`);
    lines.push(`    profile: ${snapshot.profile}`);
    lines.push(`    baseline_path: ${snapshot.baselinePath}`);
    lines.push(`    current_path: ${snapshot.currentPath}`);
    lines.push(`    sha256: ${snapshot.sha256}`);
    lines.push(`    renderer: ${snapshot.renderer}`);
    lines.push(`    pdfa_status: ${snapshot.pdfaStatus}`);
    lines.push(`    requirement_refs: [${snapshot.requirementRefs.join(", ")}]`);
  }

  return `${lines.join("\n")}\n`;
}

function resetDirectory(path: string) {
  rmSync(path, { recursive: true, force: true });
  mkdirSync(path, { recursive: true });
}

function printUsage() {
  console.log(
    "Uso: tsx apps/api/src/domain/emission/certificate-snapshots-tool.ts <write-current|write-baseline|sync>",
  );
}

function main() {
  const command = process.argv[2];
  if (!command) {
    printUsage();
    process.exitCode = 1;
    return;
  }

  switch (command) {
    case "write-current":
      syncCertificateSnapshots({ target: "current", updateManifest: false });
      console.log("certificate-snapshots: current regenerado.");
      return;
    case "write-baseline":
      syncCertificateSnapshots({ target: "baseline", updateManifest: false });
      console.log("certificate-snapshots: baseline regenerado.");
      return;
    case "sync":
      syncCertificateSnapshots({ target: "both", updateManifest: true });
      console.log("certificate-snapshots: baseline, current e manifest sincronizados.");
      return;
    default:
      printUsage();
      process.exitCode = 1;
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  main();
}
