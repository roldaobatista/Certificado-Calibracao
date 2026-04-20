import { PrismaClient } from "@prisma/client";

export type { PrismaClient } from "@prisma/client";

export function createPrismaClient(databaseUrl: string): PrismaClient {
  return new PrismaClient({
    datasources: { db: { url: databaseUrl } },
    log: [
      { level: "warn", emit: "stdout" },
      { level: "error", emit: "stdout" },
    ],
  });
}
