import {
  userDirectoryCatalogSchema,
  type UserDirectoryCatalog,
  type UserDirectoryScenario as ContractUserDirectoryScenario,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { buildUserDirectory } from "../../domain/auth/user-directory.js";
import {
  listUserDirectoryScenarios,
  resolveUserDirectoryScenario,
  type UserDirectoryScenarioDefinition,
} from "../../domain/auth/user-directory-scenarios.js";
import { requireUserDirectoryAccess } from "./auth-session.js";

const QuerySchema = z.object({
  scenario: z.string().min(1).optional(),
});

export async function registerUserDirectoryRoutes(
  app: FastifyInstance,
  persistence: CorePersistence,
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
