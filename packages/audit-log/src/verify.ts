import { createHash } from "node:crypto";

export const GENESIS_HASH = "0".repeat(64);

export interface AuditChainEntry {
  id: string;
  prevHash: string;
  payload: unknown;
  hash: string;
}

export type AuditChainInvalidReason = "prev_hash_mismatch" | "hash_mismatch";

export interface AuditChainInvalid {
  index: number;
  id: string;
  reason: AuditChainInvalidReason;
  expectedPrevHash?: string;
  actualPrevHash?: string;
  expectedHash?: string;
  actualHash?: string;
}

export interface AuditChainVerification {
  ok: boolean;
  checked: number;
  firstInvalid?: AuditChainInvalid;
}

export function computeAuditHash(prevHash: string, payload: unknown): string {
  return createHash("sha256").update(prevHash).update(canonicalJson(payload)).digest("hex");
}

export function verifyAuditHashChain(
  entries: AuditChainEntry[],
  options: { genesisHash?: string } = {},
): AuditChainVerification {
  let expectedPrevHash = options.genesisHash ?? GENESIS_HASH;

  for (let index = 0; index < entries.length; index += 1) {
    const entry = entries[index]!;
    if (entry.prevHash !== expectedPrevHash) {
      return {
        ok: false,
        checked: index + 1,
        firstInvalid: {
          index,
          id: entry.id,
          reason: "prev_hash_mismatch",
          expectedPrevHash,
          actualPrevHash: entry.prevHash,
        },
      };
    }

    const expectedHash = computeAuditHash(entry.prevHash, entry.payload);
    if (entry.hash !== expectedHash) {
      return {
        ok: false,
        checked: index + 1,
        firstInvalid: {
          index,
          id: entry.id,
          reason: "hash_mismatch",
          expectedHash,
          actualHash: entry.hash,
        },
      };
    }

    expectedPrevHash = entry.hash;
  }

  return { ok: true, checked: entries.length };
}

function canonicalJson(value: unknown): string {
  return JSON.stringify(canonicalize(value));
}

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map((item) => canonicalize(item));
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([key, item]) => [key, canonicalize(item)]),
    );
  }
  return value;
}
