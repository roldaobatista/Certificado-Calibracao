import assert from "node:assert/strict";
import { test } from "node:test";

import { buildUserDirectory, classifyCompetency } from "./user-directory.js";

test("classifies competencies as authorized expiring or expired", () => {
  const nowUtc = "2026-04-22T12:00:00Z";

  assert.equal(
    classifyCompetency(
      {
        instrumentType: "balanca",
        roleLabel: "Signatario",
        validUntilUtc: "2026-12-01T00:00:00Z",
      },
      nowUtc,
    ).status,
    "authorized",
  );
  assert.equal(
    classifyCompetency(
      {
        instrumentType: "balanca",
        roleLabel: "Revisor",
        validUntilUtc: "2026-05-20T00:00:00Z",
      },
      nowUtc,
    ).status,
    "expiring",
  );
  assert.equal(
    classifyCompetency(
      {
        instrumentType: "balanca",
        roleLabel: "Tecnico",
        validUntilUtc: "2026-03-01T00:00:00Z",
      },
      nowUtc,
    ).status,
    "expired",
  );
});

test("builds a user directory summary with active invited suspended and competency counts", () => {
  const result = buildUserDirectory({
    organizationName: "Lab. Acme",
    nowUtc: "2026-04-22T12:00:00Z",
    users: [
      {
        userId: "user-1",
        displayName: "Joao Admin",
        email: "joao@lab.com",
        roles: ["admin"],
        status: "active",
        deviceCount: 1,
        competencies: [],
      },
      {
        userId: "user-2",
        displayName: "Maria Revisora",
        email: "maria@lab.com",
        roles: ["technical_reviewer"],
        status: "invited",
        deviceCount: 0,
        competencies: [],
      },
      {
        userId: "user-3",
        displayName: "Carlos Signatario",
        email: "carlos@lab.com",
        roles: ["signatory"],
        status: "suspended",
        deviceCount: 2,
        competencies: [
          {
            instrumentType: "balanca",
            roleLabel: "Signatario",
            validUntilUtc: "2026-05-01T00:00:00Z",
          },
        ],
      },
    ],
  });

  assert.equal(result.summary.organizationName, "Lab. Acme");
  assert.equal(result.summary.activeUsers, 1);
  assert.equal(result.summary.invitedUsers, 1);
  assert.equal(result.summary.suspendedUsers, 1);
  assert.equal(result.summary.expiringCompetencies, 1);
  assert.equal(result.summary.expiredCompetencies, 0);
  assert.equal(result.summary.status, "attention");
});
