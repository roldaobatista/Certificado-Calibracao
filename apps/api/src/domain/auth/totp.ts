import { createHmac } from "node:crypto";

const BASE32_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";

function base32Encode(buffer: Buffer): string {
  let bits = 0;
  let value = 0;
  let output = "";
  for (let i = 0; i < buffer.length; i++) {
    value = (value << 8) | (buffer[i] ?? 0);
    bits += 8;
    while (bits >= 5) {
      output += BASE32_ALPHABET[(value >>> (bits - 5)) & 31];
      bits -= 5;
    }
  }
  if (bits > 0) {
    output += BASE32_ALPHABET[(value << (5 - bits)) & 31];
  }
  return output;
}

function base32Decode(encoded: string): Buffer {
  const map = new Map<string, number>();
  for (let i = 0; i < BASE32_ALPHABET.length; i++) {
    map.set(BASE32_ALPHABET[i]!, i);
  }
  let bits = 0;
  let value = 0;
  const bytes: number[] = [];
  for (const char of encoded.toUpperCase()) {
    const idx = map.get(char);
    if (idx === undefined) continue;
    value = (value << 5) | idx;
    bits += 5;
    if (bits >= 8) {
      bytes.push((value >>> (bits - 8)) & 255);
      bits -= 8;
    }
  }
  return Buffer.from(bytes);
}

function hotp(secret: Buffer, counter: bigint): string {
  const buf = Buffer.alloc(8);
  buf.writeBigUInt64BE(counter);
  const hmac = createHmac("sha1", secret).update(buf).digest();
  const offset = hmac[hmac.length - 1]! & 0x0f;
  const code =
    ((hmac[offset]! & 0x7f) << 24) |
    ((hmac[offset + 1]! & 0xff) << 16) |
    ((hmac[offset + 2]! & 0xff) << 8) |
    (hmac[offset + 3]! & 0xff);
  return (code % 1_000_000).toString().padStart(6, "0");
}

export function generateTotpSecret(): { raw: Buffer; base32: string } {
  const raw = Buffer.alloc(20);
  for (let i = 0; i < raw.length; i++) {
    raw[i] = Math.floor(Math.random() * 256);
  }
  return { raw, base32: base32Encode(raw) };
}

export function verifyTotp(base32Secret: string, code: string, window = 1): boolean {
  if (!/^\d{6}$/.test(code)) return false;
  const secret = base32Decode(base32Secret);
  const nowSec = Math.floor(Date.now() / 1000);
  const step = 30;
  const counter = BigInt(Math.floor(nowSec / step));
  for (let i = -window; i <= window; i++) {
    if (hotp(secret, counter + BigInt(i)) === code) {
      return true;
    }
  }
  return false;
}

export function generateCurrentTotpCode(base32Secret: string): string {
  const secret = base32Decode(base32Secret);
  const nowSec = Math.floor(Date.now() / 1000);
  const step = 30;
  const counter = BigInt(Math.floor(nowSec / step));
  return hotp(secret, counter);
}

export function generateTotpUri(secret: string, account: string, issuer: string): string {
  const label = encodeURIComponent(`${issuer}:${account}`);
  const params = new URLSearchParams({
    secret,
    issuer,
    algorithm: "SHA1",
    digits: "6",
    period: "30",
  });
  return `otpauth://totp/${label}?${params.toString()}`;
}
