import fs from "node:fs";
import path from "node:path";
import yaml from "js-yaml";
import { z } from "zod";

export const routeAuthorizationEntrySchema = z.object({
  route: z.string().min(1),
  method: z.enum(["GET", "POST", "PUT", "PATCH", "DELETE"]),
  public: z.boolean().optional().default(false),
  roles: z.array(z.string()).optional().default([]),
  csrf: z.boolean().optional().default(false),
  audit: z.boolean().optional().default(false),
  tenant: z.boolean().optional().default(false),
  rateLimit: z
    .object({
      max: z.number().int().positive(),
      windowMs: z.number().int().positive(),
    })
    .optional(),
});

export const routeAuthorizationMatrixSchema = z.array(routeAuthorizationEntrySchema);

export type RouteAuthorizationEntry = z.infer<typeof routeAuthorizationEntrySchema>;
export type RouteAuthorizationMatrix = z.infer<typeof routeAuthorizationMatrixSchema>;

const matrixPath = path.resolve(import.meta.dirname, "route-authorization-matrix.yaml");

export function loadRouteAuthorizationMatrix(): RouteAuthorizationMatrix {
  const content = fs.readFileSync(matrixPath, "utf-8");
  const parsed = yaml.load(content);
  return routeAuthorizationMatrixSchema.parse(parsed);
}

export function findRouteEntry(
  matrix: RouteAuthorizationMatrix,
  route: string,
  method: string,
): RouteAuthorizationEntry | undefined {
  return matrix.find((entry) => entry.route === route && entry.method === method.toUpperCase());
}
