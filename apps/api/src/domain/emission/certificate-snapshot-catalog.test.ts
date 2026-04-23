import assert from "node:assert/strict";
import { existsSync, mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";

import { listCanonicalCertificateSnapshots } from "./certificate-snapshot-catalog.js";
import { renderSnapshotManifest, syncCertificateSnapshots } from "./certificate-snapshots-tool.js";

test("builds a canonical battery with 30 certificate snapshots and 10 per profile", () => {
  const snapshots = listCanonicalCertificateSnapshots();
  const counts = new Map<string, number>();

  for (const snapshot of snapshots) {
    counts.set(snapshot.profile, (counts.get(snapshot.profile) ?? 0) + 1);
    assert.match(snapshot.id, /^profile-[abc]-\d{2}$/);
    assert.match(snapshot.baselinePath, /baseline\/profile-[abc]-\d{2}\.pdf$/);
    assert.match(snapshot.currentPath, /current\/profile-[abc]-\d{2}\.pdf$/);
    assert.equal(snapshot.bytes.length > 500, true);
  }

  assert.equal(snapshots.length, 30);
  assert.equal(counts.get("A"), 10);
  assert.equal(counts.get("B"), 10);
  assert.equal(counts.get("C"), 10);
});

test("renders manifest text with the deterministic pdf renderer and 10 snapshots per profile", () => {
  const manifest = renderSnapshotManifest();

  assert.match(manifest, /snapshots_per_profile: 10/);
  assert.match(manifest, /renderer: deterministic-pdf-v1/);
  assert.match(manifest, /pdfa_status: pending_external_validation/);
  assert.match(manifest, /profile-a-01/);
  assert.match(manifest, /profile-c-10/);
});

test("syncs baseline, current and manifest for the canonical battery", () => {
  const root = mkdtempSync(join(tmpdir(), "afere-snapshots-"));
  const snapshotsRoot = resolve(root, "compliance", "validation-dossier", "snapshots");
  const generated = syncCertificateSnapshots({ root, target: "both", updateManifest: true });

  assert.equal(generated.length, 30);
  assert.equal(existsSync(resolve(snapshotsRoot, "manifest.yaml")), true);
  assert.equal(existsSync(resolve(snapshotsRoot, "baseline", "profile-a-01.pdf")), true);
  assert.equal(existsSync(resolve(snapshotsRoot, "current", "profile-c-10.pdf")), true);

  const manifest = readFileSync(resolve(snapshotsRoot, "manifest.yaml"), "utf8");
  assert.match(manifest, /profile-b-05/);
});
