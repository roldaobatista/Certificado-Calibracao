/**
 * Abstract KMS interface for signing and verification.
 * Production requires a real HSM or cloud KMS (AWS KMS, Azure Key Vault, etc.).
 */

export interface KmsKeyPair {
  keyId: string;
  algorithm: "RSASSA-PSS-SHA256" | "ECDSA-P256-SHA256";
  createdAt: Date;
}

export interface KmsSignInput {
  keyId: string;
  data: Buffer;
  digestAlgorithm?: "SHA256" | "SHA384" | "SHA512";
}

export interface KmsSignOutput {
  signature: Buffer;
  keyId: string;
  algorithm: string;
}

export interface KmsVerifyInput {
  keyId: string;
  data: Buffer;
  signature: Buffer;
  digestAlgorithm?: "SHA256" | "SHA384" | "SHA512";
}

export interface KmsVerifyOutput {
  valid: boolean;
  keyId: string;
}

export interface KmsProvider {
  generateKeyPair(algorithm: KmsKeyPair["algorithm"]): Promise<KmsKeyPair>;
  sign(input: KmsSignInput): Promise<KmsSignOutput>;
  verify(input: KmsVerifyInput): Promise<KmsVerifyOutput>;
  getPublicKey(keyId: string): Promise<Buffer>;
}

// Stub implementation for development only.
// DO NOT use in production — it uses software crypto without secure key storage.
export function createDevKmsProvider(): KmsProvider {
  const keys = new Map<string, CryptoKeyPair>();

  return {
    async generateKeyPair(algorithm) {
      const keyId = `dev-key-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const subtle = crypto.subtle;
      const isEc = algorithm === "ECDSA-P256-SHA256";
      const pair = await subtle.generateKey(
        isEc
          ? { name: "ECDSA", namedCurve: "P-256" }
          : { name: "RSA-PSS", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" },
        true,
        ["sign", "verify"],
      );
      keys.set(keyId, pair as CryptoKeyPair);
      return { keyId, algorithm, createdAt: new Date() };
    },
    async sign(input) {
      const pair = keys.get(input.keyId);
      if (!pair) throw new Error(`Key not found: ${input.keyId}`);
      const subtle = crypto.subtle;
      const alg = pair.privateKey.algorithm;
      const sig = await subtle.sign(
        alg.name === "ECDSA" ? { name: "ECDSA", hash: "SHA-256" } : { name: "RSA-PSS", saltLength: 32 },
        pair.privateKey,
        input.data,
      );
      return { signature: Buffer.from(sig), keyId: input.keyId, algorithm: alg.name };
    },
    async verify(input) {
      const pair = keys.get(input.keyId);
      if (!pair) return { valid: false, keyId: input.keyId };
      const subtle = crypto.subtle;
      const alg = pair.publicKey.algorithm;
      const valid = await subtle.verify(
        alg.name === "ECDSA" ? { name: "ECDSA", hash: "SHA-256" } : { name: "RSA-PSS", saltLength: 32 },
        pair.publicKey,
        input.signature,
        input.data,
      );
      return { valid, keyId: input.keyId };
    },
    async getPublicKey(keyId) {
      const pair = keys.get(keyId);
      if (!pair) throw new Error(`Key not found: ${keyId}`);
      const subtle = crypto.subtle;
      const exported = await subtle.exportKey("spki", pair.publicKey);
      return Buffer.from(exported);
    },
  };
}
