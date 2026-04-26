/**
 * Abstract storage interface for PDFs and attachments.
 * Production requires S3, Azure Blob, GCS, or similar with encryption at rest.
 */

export interface StorageUploadInput {
  key: string;
  body: Buffer;
  contentType: string;
  metadata?: Record<string, string>;
}

export interface StorageUploadOutput {
  key: string;
  url: string;
  etag?: string;
}

export interface StorageDownloadOutput {
  body: Buffer;
  contentType: string;
  metadata: Record<string, string>;
}

export interface StorageProvider {
  upload(input: StorageUploadInput): Promise<StorageUploadOutput>;
  download(key: string): Promise<StorageDownloadOutput>;
  delete(key: string): Promise<void>;
  exists(key: string): Promise<boolean>;
  getSignedUrl(key: string, expiresInSeconds: number): Promise<string>;
}

// Stub implementation for development.
// Stores files in memory only — all data is lost on restart.
export function createDevStorageProvider(): StorageProvider {
  const store = new Map<string, { body: Buffer; contentType: string; metadata: Record<string, string> }>();

  return {
    async upload(input) {
      store.set(input.key, { body: input.body, contentType: input.contentType, metadata: input.metadata ?? {} });
      return { key: input.key, url: `dev://storage/${input.key}` };
    },
    async download(key) {
      const item = store.get(key);
      if (!item) throw new Error(`Object not found: ${key}`);
      return { body: item.body, contentType: item.contentType, metadata: item.metadata };
    },
    async delete(key) {
      store.delete(key);
    },
    async exists(key) {
      return store.has(key);
    },
    async getSignedUrl(key, expiresInSeconds) {
      const item = store.get(key);
      if (!item) throw new Error(`Object not found: ${key}`);
      return `dev://storage/${key}?expires=${Date.now() + expiresInSeconds * 1000}`;
    },
  };
}
