import { scryptSync, timingSafeEqual } from "node:crypto";

const SCRYPT_KEY_LENGTH = 64;
const SCRYPT_MAX_MEM = 64 * 1024 * 1024;

type PasswordHashParts = {
  n: number;
  r: number;
  p: number;
  salt: string;
  digest: string;
};

export function hashPassword(password: string, salt: string): string {
  const digest = scryptSync(password, salt, SCRYPT_KEY_LENGTH, {
    N: 16384,
    r: 8,
    p: 1,
    maxmem: SCRYPT_MAX_MEM,
  }).toString("base64url");

  return `scrypt:v1:16384:8:1:${salt}:${digest}`;
}

export function verifyPassword(password: string, encodedHash: string): boolean {
  const parsed = parsePasswordHash(encodedHash);
  if (!parsed) {
    return false;
  }

  const candidate = scryptSync(password, parsed.salt, SCRYPT_KEY_LENGTH, {
    N: parsed.n,
    r: parsed.r,
    p: parsed.p,
    maxmem: SCRYPT_MAX_MEM,
  });
  const expected = Buffer.from(parsed.digest, "base64url");

  if (candidate.length !== expected.length) {
    return false;
  }

  return timingSafeEqual(candidate, expected);
}

function parsePasswordHash(value: string): PasswordHashParts | null {
  const parts = value.split(":");
  if (parts.length !== 7) {
    return null;
  }

  const [algorithm, version, n, r, p, salt, digest] = parts;
  if (algorithm !== "scrypt" || version !== "v1") {
    return null;
  }

  const parsed = {
    n: Number.parseInt(n ?? "", 10),
    r: Number.parseInt(r ?? "", 10),
    p: Number.parseInt(p ?? "", 10),
    salt: salt ?? "",
    digest: digest ?? "",
  };

  if (
    !Number.isInteger(parsed.n) ||
    !Number.isInteger(parsed.r) ||
    !Number.isInteger(parsed.p) ||
    parsed.salt.length === 0 ||
    parsed.digest.length === 0
  ) {
    return null;
  }

  return parsed;
}
