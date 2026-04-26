import assert from "node:assert/strict";
import { test } from "node:test";

import { buildApp } from "../../app.js";
import type { Env } from "../../config/env.js";
import { createMemoryCorePersistence } from "../../domain/auth/core-persistence.js";
import { hashSessionToken } from "../../domain/auth/session-auth.js";
import { createMemoryQualityPersistence } from "../../domain/quality/quality-persistence.js";
import { createMemoryRegistryPersistence } from "../../domain/registry/registry-persistence.js";
import { createMemoryServiceOrderPersistence } from "../../domain/emission/service-order-persistence.js";

const TEST_ENV: Env = {
  NODE_ENV: "test",
  LOG_LEVEL: "fatal",
  HOST: "127.0.0.1",
  PORT: 3000,
  CORS_ORIGINS: [],
  DATABASE_URL: "postgresql://afere:afere@localhost:5432/afere?schema=public",
  REDIS_URL: "redis://localhost:6379",
  ALLOW_SCENARIO_ROUTES: true,
  RATE_LIMIT_MAX: 100,
  RATE_LIMIT_WINDOW_MS: 60000,
  COOKIE_SECRET: "test-cookie-secret-32-chars-long-ok",
  REDIRECT_ALLOWLIST: ["/auth/login", "/auth/logout", "/onboarding", "/emission/workspace", "/emission/review-signature", "/emission/signature-queue", "/dashboard"],
};

test("auth negative: login with wrong password returns 401", async () => {
  const app = await buildApp({
    env: TEST_ENV,
    corePersistence: createMemoryCorePersistence({
      users: [
        {
          userId: "user-1",
          organizationId: "org-1",
          organizationName: "Lab",
          organizationSlug: "lab",
          email: "admin@afere.local",
          passwordHash: "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$somehash",
          displayName: "Admin",
          roles: ["admin"],
          status: "active",
          mfaEnforced: false,
          mfaEnrolled: false,
          deviceCount: 1,
          competencies: [],
        },
      ],
    }),
    registryPersistence: createMemoryRegistryPersistence(),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(),
    qualityPersistence: createMemoryQualityPersistence(),
  });

  const response = await app.inject({
    method: "POST",
    url: "/auth/login",
    payload: { email: "admin@afere.local", password: "wrong-password" },
  });

  assert.equal(response.statusCode, 401);
  assert.equal(JSON.parse(response.payload).reason, "invalid_credentials");
});

test("auth negative: login with non-existent email returns 401", async () => {
  const app = await buildApp({
    env: TEST_ENV,
    corePersistence: createMemoryCorePersistence(),
    registryPersistence: createMemoryRegistryPersistence(),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(),
    qualityPersistence: createMemoryQualityPersistence(),
  });

  const response = await app.inject({
    method: "POST",
    url: "/auth/login",
    payload: { email: "nobody@afere.local", password: "AnyPassword123!" },
  });

  assert.equal(response.statusCode, 401);
  assert.equal(JSON.parse(response.payload).reason, "invalid_credentials");
});

test("auth negative: protected route without session returns 401", async () => {
  const app = await buildApp({
    env: TEST_ENV,
    corePersistence: createMemoryCorePersistence(),
    registryPersistence: createMemoryRegistryPersistence(),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(),
    qualityPersistence: createMemoryQualityPersistence(),
  });

  const response = await app.inject({
    method: "GET",
    url: "/emission/workspace",
  });

  assert.equal(response.statusCode, 401);
});

test("auth negative: bootstrap disabled after first organization", async () => {
  const corePersistence = createMemoryCorePersistence();
  const app = await buildApp({
    env: TEST_ENV,
    corePersistence,
    registryPersistence: createMemoryRegistryPersistence(),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(),
    qualityPersistence: createMemoryQualityPersistence(),
  });

  // Primeiro bootstrap deve funcionar
  const first = await app.inject({
    method: "POST",
    url: "/onboarding/bootstrap",
    payload: {
      slug: "lab-test",
      legalName: "Laboratorio Teste",
      regulatoryProfile: "type_b",
      adminName: "Admin",
      adminEmail: "admin@test.local",
      password: "Password123!",
    },
  });

  assert.equal(first.statusCode, 302);

  // Segundo bootstrap deve ser bloqueado
  const second = await app.inject({
    method: "POST",
    url: "/onboarding/bootstrap",
    payload: {
      slug: "lab-test-2",
      legalName: "Laboratorio Teste 2",
      regulatoryProfile: "type_b",
      adminName: "Admin 2",
      adminEmail: "admin2@test.local",
      password: "Password123!",
    },
  });

  assert.equal(second.statusCode, 403);
  assert.equal(JSON.parse(second.payload).error, "bootstrap_disabled");
});

test("auth negative: redirect to external URL is rejected", async () => {
  const app = await buildApp({
    env: TEST_ENV,
    corePersistence: createMemoryCorePersistence({
      users: [
        {
          userId: "user-1",
          organizationId: "org-1",
          organizationName: "Lab",
          organizationSlug: "lab",
          email: "admin@afere.local",
          passwordHash: "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$somehash",
          displayName: "Admin",
          roles: ["admin"],
          status: "active",
          mfaEnforced: false,
          mfaEnrolled: false,
          deviceCount: 1,
          competencies: [],
        },
      ],
    }),
    registryPersistence: createMemoryRegistryPersistence(),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(),
    qualityPersistence: createMemoryQualityPersistence(),
  });

  const response = await app.inject({
    method: "POST",
    url: "/auth/login",
    payload: { email: "admin@afere.local", password: "wrong-password", redirectTo: "https://evil.com" },
  });

  // Deve retornar 401 (credenciais erradas) e NÃO redirect para evil.com
  assert.equal(response.statusCode, 401);
  assert.equal(response.headers.location, undefined);
});

test("auth negative: redirect with javascript scheme is rejected", async () => {
  const app = await buildApp({
    env: TEST_ENV,
    corePersistence: createMemoryCorePersistence({
      users: [
        {
          userId: "user-1",
          organizationId: "org-1",
          organizationName: "Lab",
          organizationSlug: "lab",
          email: "admin@afere.local",
          passwordHash: "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$somehash",
          displayName: "Admin",
          roles: ["admin"],
          status: "active",
          mfaEnforced: false,
          mfaEnrolled: false,
          deviceCount: 1,
          competencies: [],
        },
      ],
    }),
    registryPersistence: createMemoryRegistryPersistence(),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(),
    qualityPersistence: createMemoryQualityPersistence(),
  });

  const login = await app.inject({
    method: "POST",
    url: "/auth/login",
    payload: { email: "admin@afere.local", password: "wrong-password", redirectTo: "javascript:alert(1)" },
  });

  assert.equal(login.statusCode, 401);
  assert.equal(login.headers.location, undefined);
});

test("auth negative: technician cannot access admin-only route", async () => {
  const corePersistence = createMemoryCorePersistence({
    users: [
      {
        userId: "user-tech",
        organizationId: "org-1",
        organizationName: "Lab",
        organizationSlug: "lab",
        email: "tech@afere.local",
        passwordHash: "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$somehash",
        displayName: "Tecnico",
        roles: ["technician"],
        status: "active",
        mfaEnforced: false,
        mfaEnrolled: false,
        deviceCount: 1,
        competencies: [],
      },
    ],
  });

  const token = "test-session-token-32-chars-long-ok";
  const tokenHash = hashSessionToken(token);
  await corePersistence.createSession({
    organizationId: "org-1",
    userId: "user-tech",
    tokenHash,
    expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
  });

  const app = await buildApp({
    env: TEST_ENV,
    corePersistence,
    registryPersistence: createMemoryRegistryPersistence(),
    serviceOrderPersistence: createMemoryServiceOrderPersistence(),
    qualityPersistence: createMemoryQualityPersistence(),
  });

  const response = await app.inject({
    method: "GET",
    url: "/settings/organization",
    headers: { cookie: `afere_session=${token}` },
  });

  assert.equal(response.statusCode, 403);
});
