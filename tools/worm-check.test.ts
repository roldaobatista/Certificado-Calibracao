import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { scanWormStorage } from "./worm-check.js";

function makeWorkspace(): string {
  const root = mkdtempSync(join(tmpdir(), "afere-worm-check-"));
  mkdirSync(join(root, "infra"), { recursive: true });
  writeFileSync(join(root, "pnpm-workspace.yaml"), "packages:\n  - packages/*\n");
  return root;
}

test("flags regulatory S3 bucket without object lock", async () => {
  const root = makeWorkspace();
  try {
    writeFileSync(
      join(root, "infra", "main.tf"),
      `resource "aws_s3_bucket" "certificates" {
  bucket = "afere-certificates"
}
`,
    );

    const result = await scanWormStorage({ cwd: root });

    assert.equal(result.errors, 1);
    assert.equal(result.findings[0]?.ruleId, "WORM-001");
    assert.equal(result.findings[0]?.resource, "aws_s3_bucket.certificates");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("allows regulatory S3 bucket with object lock enabled", async () => {
  const root = makeWorkspace();
  try {
    writeFileSync(
      join(root, "infra", "main.tf"),
      `resource "aws_s3_bucket" "certificates" {
  bucket = "afere-certificates"
  object_lock_enabled = true
}
`,
    );

    const result = await scanWormStorage({ cwd: root });

    assert.equal(result.errors, 0);
    assert.equal(result.findings.length, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("ignores non-regulatory mutable backup buckets", async () => {
  const root = makeWorkspace();
  try {
    writeFileSync(
      join(root, "infra", "main.tf"),
      `resource "aws_s3_bucket" "postgres_backups" {
  bucket = "afere-postgres-backups"
}
`,
    );

    const result = await scanWormStorage({ cwd: root });

    assert.equal(result.errors, 0);
    assert.equal(result.findings.length, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("flags B2 audit checkpoint bucket without file lock", async () => {
  const root = makeWorkspace();
  try {
    writeFileSync(
      join(root, "infra", "b2.tf"),
      `resource "b2_bucket" "audit_checkpoints" {
  bucket_name = "afere-audit-checkpoints"
  bucket_type = "allPrivate"
}
`,
    );

    const result = await scanWormStorage({ cwd: root });

    assert.equal(result.errors, 1);
    assert.equal(result.findings[0]?.ruleId, "WORM-002");
    assert.equal(result.findings[0]?.resource, "b2_bucket.audit_checkpoints");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
