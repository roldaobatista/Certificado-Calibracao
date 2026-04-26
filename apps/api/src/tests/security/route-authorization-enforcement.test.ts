import assert from "node:assert/strict";
import { test } from "node:test";

import { buildApp } from "../../app.js";
import { createMemoryCorePersistence } from "../../domain/auth/core-persistence.js";
import { createMemoryRegistryPersistence } from "../../domain/registry/registry-persistence.js";
import { createMemoryServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";
import { createMemoryQualityPersistence } from "../../domain/quality/quality-persistence.js";
import { createRuntimeReadinessStub, TEST_ENV, normalizeCookieHeader, createV1MemorySeed } from "../integration/helpers.js";

test("public mutable route allows unauthenticated access", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "POST",
      url: "/auth/login",
      payload: { email: "nobody@afere.local", password: "wrong" },
    });

    // Even with wrong credentials, the route is public so the hook lets it through.
    // The handler may return 400 (validation) or 401 (bad credentials), but never 503 from the hook.
    assert.notEqual(response.statusCode, 503);
    assert.notEqual(response.json().error, "route_not_in_authorization_matrix");
  } finally {
    await app.close();
  }
});

test("authenticated mutable route without session returns 401", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "POST",
      url: "/auth/logout",
    });

    assert.equal(response.statusCode, 401);
    assert.equal(response.json().error, "authentication_required");
  } finally {
    await app.close();
  }
});

test("role-restricted mutable route with insufficient role returns 403", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({
    env: TEST_ENV,
    runtimeReadiness,
    corePersistence: createMemoryCorePersistence(createV1MemorySeed()),
    registryPersistence: createMemoryRegistryPersistence(),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(),
    qualityPersistence: createMemoryQualityPersistence(),
  });

  try {
    // Use the seeded reviewer user (technical_reviewer, not admin)
    const login = await app.inject({
      method: "POST",
      url: "/auth/login",
      payload: { email: "revisora@afere.local", password: "Afere@2026!" },
    });
    const cookie = normalizeCookieHeader(login.headers["set-cookie"]);
    assert.ok(cookie);

    // POST /auth/users/manage requires admin role
    const response = await app.inject({
      method: "POST",
      url: "/auth/users/manage",
      headers: { cookie },
      payload: { action: "save", email: "x@x.com", displayName: "X", roles: ["technician"], status: "active", mfaEnforced: false, mfaEnrolled: false, deviceCount: 0 },
    });

    assert.equal(response.statusCode, 403);
    assert.equal(response.json().error, "forbidden");
  } finally {
    await app.close();
  }
});

test("mutable route missing from matrix returns 503 fail-closed", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    // Register a temporary route that is not in the authorization matrix
    app.post("/__test-unmapped-route", async (_request, reply) => {
      return reply.code(200).send({ ok: true });
    });

    const response = await app.inject({
      method: "POST",
      url: "/__test-unmapped-route",
    });

    assert.equal(response.statusCode, 503);
    assert.equal(response.json().error, "route_not_in_authorization_matrix");
  } finally {
    await app.close();
  }
});

test("GET public route in matrix returns 200", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/healthz",
    });

    assert.equal(response.statusCode, 200);
  } finally {
    await app.close();
  }
});

test("GET private route in matrix without session returns 401", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    const response = await app.inject({
      method: "GET",
      url: "/emission/workspace",
    });

    assert.equal(response.statusCode, 401);
    assert.equal(response.json().error, "authentication_required");
  } finally {
    await app.close();
  }
});

test("GET route missing from matrix returns 503 fail-closed", async () => {
  const { runtimeReadiness } = createRuntimeReadinessStub();
  const app = await buildApp({ env: TEST_ENV, runtimeReadiness });

  try {
    app.get("/__test-unmapped-get", async (_request, reply) => {
      return reply.code(200).send({ ok: true });
    });

    const response = await app.inject({
      method: "GET",
      url: "/__test-unmapped-get",
    });

    assert.equal(response.statusCode, 503);
    assert.equal(response.json().error, "route_not_in_authorization_matrix");
  } finally {
    await app.close();
  }
});
