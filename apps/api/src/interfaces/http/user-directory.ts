import { randomBytes } from "node:crypto";

import {
  membershipRoleSchema,
  userDirectoryCatalogSchema,
  userLifecycleStatusSchema,
  type MembershipRole,
  type UserDirectoryCatalog,
  type UserDirectoryScenario as ContractUserDirectoryScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import type { Env } from "../../config/env.js";
import { hashPassword } from "../../domain/auth/password.js";
import { buildUserDirectory } from "../../domain/auth/user-directory.js";
import {
  listUserDirectoryScenarios,
  resolveUserDirectoryScenario,
  type UserDirectoryScenarioDefinition,
} from "../../domain/auth/user-directory-scenarios.js";
import { requireUserDirectoryAccess } from "./auth-session.js";
import { isRedirectAllowed } from "./redirect-helpers.js";
import {
  isConflictError,
  readRedirectTarget,
  toBoolean,
  toNumber,
  toOptionalString,
  toStringArray,
} from "./form-helpers.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
});

const SaveUserBodySchema = z.object({
  action: z.literal("save"),
  userId: z.preprocess(toOptionalString, z.string().min(1).optional()),
  email: z.string().email(),
  password: z.preprocess(toOptionalString, z.string().min(8).optional()),
  displayName: z.string().min(3),
  roles: z.preprocess(toStringArray, z.array(membershipRoleSchema).min(1)),
  status: userLifecycleStatusSchema,
  teamName: z.preprocess(toOptionalString, z.string().min(1).optional()),
  mfaEnforced: z.preprocess(toBoolean, z.boolean()),
  mfaEnrolled: z.preprocess(toBoolean, z.boolean()),
  deviceCount: z.preprocess(toNumber, z.number().int().nonnegative()),
  competenciesText: z.preprocess(toOptionalString, z.string().min(1).optional()),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

const ToggleUserBodySchema = z.object({
  action: z.enum(["archive", "restore"]),
  userId: z.string().min(1),
  redirectTo: z.preprocess(toOptionalString, z.string().min(1).optional()),
});

const ManageUserBodySchema = z.discriminatedUnion("action", [
  SaveUserBodySchema,
  ToggleUserBodySchema,
]);

export async function registerUserDirectoryRoutes(
  app: FastifyInstance,
  persistence: CorePersistence,
  env: Env,
) {
  app.get("/auth/users", async (request, reply) => {
    const query = QuerySchema.safeParse(request.query);
    if (!query.success) {
      return reply.code(400).send({ error: "invalid_query" });
    }

    if (!query.data.scenario) {
      const context = await requireUserDirectoryAccess(request, reply, persistence);
      if (!context) {
        return reply;
      }

      const users = await persistence.listUsersByOrganization(context.user.organizationId);
      const directory = buildUserDirectory({
        organizationName: context.user.organizationName,
        nowUtc: new Date().toISOString(),
        users: users.map((user) => ({
          userId: user.userId,
          displayName: user.displayName,
          email: user.email,
          roles: user.roles,
          status: user.status,
          teamName: user.teamName,
          lastLoginUtc: user.lastLoginUtc,
          deviceCount: user.deviceCount,
          competencies: user.competencies.map((competency) => ({
            instrumentType: competency.instrumentType,
            roleLabel: competency.roleLabel,
            validUntilUtc: competency.validUntilUtc,
          })),
        })),
      });

      const selectedScenarioId =
        directory.summary.suspendedUsers > 0 || directory.summary.expiredCompetencies > 0
          ? "suspended-access"
          : directory.summary.expiringCompetencies > 0
            ? "expiring-competencies"
            : "operational-team";

      const payload: UserDirectoryCatalog = userDirectoryCatalogSchema.parse({
        selectedScenarioId,
        scenarios: [
          {
            id: selectedScenarioId,
            label: "Diretorio persistido do tenant",
            description: `Equipe ${context.user.organizationName} carregada do banco multitenant.`,
            summary: directory.summary,
            users: directory.users,
          },
        ],
      });

      return reply.code(200).send(payload);
    }

    const selectedScenario = resolveUserDirectoryScenario(query.data.scenario);
    const payload: UserDirectoryCatalog = userDirectoryCatalogSchema.parse({
      selectedScenarioId: selectedScenario.id,
      scenarios: listUserDirectoryScenarios().map(toContractScenario),
    });

    return reply.code(200).send(payload);
  });

  app.post("/auth/users/manage", async (request, reply) => {
    const context = await requireUserDirectoryAccess(request, reply, persistence);
    if (!context) {
      return reply;
    }

    const body = ManageUserBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    try {
      if (body.data.action === "save") {
        if (!body.data.userId && !body.data.password) {
          return reply.code(400).send({ error: "password_required" });
        }

        await persistence.saveUser({
          organizationId: context.user.organizationId,
          userId: body.data.userId,
          actorUserId: context.user.userId,
          email: body.data.email,
          passwordHash: body.data.password
            ? hashPassword(body.data.password, randomBytes(16).toString("base64url"))
            : undefined,
          displayName: body.data.displayName,
          roles: body.data.roles,
          status: body.data.status,
          teamName: body.data.teamName,
          mfaEnforced: body.data.mfaEnforced,
          mfaEnrolled: body.data.mfaEnrolled,
          deviceCount: body.data.deviceCount,
          competencies: parseCompetencies(body.data.competenciesText),
        });
      } else {
        await persistence.setUserStatus(
          context.user.organizationId,
          body.data.userId,
          body.data.action === "archive" ? "suspended" : "active",
          context.user.userId,
        );
      }
    } catch (error) {
      if (isConflictError(error)) {
        return reply.code(409).send({ error: "user_directory_conflict" });
      }

      throw error;
    }

    const redirectTo = readRedirectTarget(request.body);
    if (redirectTo && isRedirectAllowed(redirectTo, env.REDIRECT_ALLOWLIST)) {
      return reply.redirect(redirectTo);
    }

    return reply.code(204).send();
  });
}

function toContractScenario(
  scenario: UserDirectoryScenarioDefinition,
): ContractUserDirectoryScenario {
  return {
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    summary: scenario.summary,
    users: scenario.users,
  };
}

function parseCompetencies(value: string | undefined) {
  if (!value) {
    return [];
  }

  return value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .flatMap((line) => {
      const [instrumentType, roleLabel, validUntil] = line.split("|").map((part) => part?.trim() ?? "");
      if (!instrumentType || !roleLabel || !validUntil) {
        return [];
      }

      const normalizedDate = validUntil.includes("T") ? validUntil : `${validUntil}T00:00:00.000Z`;
      const parsedDate = new Date(normalizedDate);
      if (Number.isNaN(parsedDate.getTime())) {
        return [];
      }

      return [
        {
          instrumentType,
          roleLabel,
          validUntil: parsedDate,
        },
      ];
    });
}
