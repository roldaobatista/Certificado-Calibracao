import assert from "node:assert/strict";
import { test } from "node:test";

import { buildApp } from "../../app.js";
import { loadRouteAuthorizationMatrix, findRouteEntry } from "../../config/route-authorization-matrix.js";
import { createMemoryCorePersistence } from "../../domain/auth/core-persistence.js";
import { createMemoryServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import { createMemoryQualityPersistence } from "../../domain/quality/quality-persistence.js";
import { createMemoryRegistryPersistence } from "../../domain/registry/registry-persistence.js";
import { createRuntimeReadinessStub, TEST_ENV } from "./helpers.js";

const MUTABLE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

function extractRoutesFromPrintRoutes(printOutput: string): Array<{ method: string; route: string }> {
  const routes: Array<{ method: string; route: string }> = [];
  const lines = printOutput.split("\n");
  const stack: { prefix: string; indent: number }[] = [];

  for (const line of lines) {
    // Match the tree structure: "├── /path (GET, POST)" or "└── /path (GET)"
    const match = line.match(/^(\s*)(?:├──|└──|──)\s*(\S+)\s*\(([A-Z,\s]+)\)/);
    if (!match) continue;

    const indent = match[1]!.length;
    const segment = match[2]!;
    const methods = match[3]!.split(",").map((m) => m.trim());

    // Pop stack while current indent is <= previous indent
    while (stack.length > 0 && indent <= stack[stack.length - 1]!.indent) {
      stack.pop();
    }

    const parentPrefix = stack.length > 0 ? stack[stack.length - 1]!.prefix : "";
    const fullPath = parentPrefix + segment;
    stack.push({ prefix: fullPath, indent });

    for (const method of methods) {
      if (method && method !== "HEAD") {
        routes.push({ method, route: fullPath });
      }
    }
  }

  return routes;
}

test("every mutable HTTP route has an entry in the route authorization matrix", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(),
    registryPersistence: createMemoryRegistryPersistence(),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(),
    qualityPersistence: createMemoryQualityPersistence(),
  });

  try {
    const matrix = loadRouteAuthorizationMatrix();
    const printOutput = app.printRoutes();
    const routes = extractRoutesFromPrintRoutes(printOutput);
    const mutableRoutes = routes.filter((r) => MUTABLE_METHODS.has(r.method));

    const missing: Array<{ method: string; route: string }> = [];
    for (const route of mutableRoutes) {
      const entry = findRouteEntry(matrix, route.route, route.method);
      if (!entry) {
        missing.push(route);
      }
    }

    assert.deepStrictEqual(
      missing,
      [],
      `Missing route authorization matrix entries for mutable routes: ${JSON.stringify(missing)}`,
    );
  } finally {
    await app.close();
  }
});

test("route authorization matrix has no duplicate route+method entries", async () => {
  const matrix = loadRouteAuthorizationMatrix();
  const seen = new Set<string>();
  const duplicates: string[] = [];

  for (const entry of matrix) {
    const key = `${entry.method} ${entry.route}`;
    if (seen.has(key)) {
      duplicates.push(key);
    }
    seen.add(key);
  }

  assert.deepStrictEqual(duplicates, [], `Duplicate matrix entries: ${JSON.stringify(duplicates)}`);
});

test("every mutable matrix entry declares either public or authenticated", async () => {
  const matrix = loadRouteAuthorizationMatrix();
  const mutableMethods = new Set(["POST", "PUT", "PATCH", "DELETE"]);

  const bad: Array<{ route: string; method: string }> = [];
  for (const entry of matrix) {
    if (mutableMethods.has(entry.method)) {
      // Must be either public, or have explicit roles, or be explicitly authenticated without roles (e.g. logout, mfa)
      const authenticatedWithoutRoles = ["/auth/logout", "/auth/mfa/verify", "/auth/mfa/recover", "/auth/mfa/enroll", "/auth/mfa/confirm-enrollment"];
      if (!entry.public && entry.roles.length === 0 && !authenticatedWithoutRoles.includes(entry.route)) {
        bad.push({ route: entry.route, method: entry.method });
      }
    }
  }

  assert.deepStrictEqual(
    bad,
    [],
    `Mutable routes must declare public, roles, or be an authenticated route: ${JSON.stringify(bad)}`,
  );
});
