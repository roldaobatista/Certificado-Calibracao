import type {
  UserDirectoryCatalog,
  UserDirectoryScenario,
  UserDirectoryScenarioId,
} from "@afere/contracts";

import { buildUserDirectory, type DirectoryUserInput } from "./user-directory.js";

const ADMIN_USER: DirectoryUserInput = {
  userId: "user-admin-1",
  displayName: "Joao Admin",
  email: "joao@lab-acme.com.br",
  roles: ["admin"],
  status: "active",
  teamName: "Gestao",
  lastLoginUtc: "2026-04-22T08:10:00Z",
  deviceCount: 1,
  competencies: [],
};

const TECHNICIAN_USER: DirectoryUserInput = {
  userId: "user-tech-1",
  displayName: "Lia Tecnica",
  email: "lia@lab-acme.com.br",
  roles: ["technician"],
  status: "active",
  teamName: "Campo SP",
  lastLoginUtc: "2026-04-22T09:20:00Z",
  deviceCount: 2,
  competencies: [
    {
      instrumentType: "balanca",
      roleLabel: "Tecnico calibrador",
      validUntilUtc: "2026-12-20T00:00:00Z",
    },
  ],
};

const REVIEWER_USER: DirectoryUserInput = {
  userId: "user-reviewer-1",
  displayName: "Maria Revisora",
  email: "maria@lab-acme.com.br",
  roles: ["technical_reviewer"],
  status: "active",
  teamName: "Qualidade",
  lastLoginUtc: "2026-04-22T08:55:00Z",
  deviceCount: 1,
  competencies: [
    {
      instrumentType: "balanca",
      roleLabel: "Revisor tecnico",
      validUntilUtc: "2026-11-10T00:00:00Z",
    },
  ],
};

const SIGNATORY_USER: DirectoryUserInput = {
  userId: "user-signatory-1",
  displayName: "Carlos Signatario",
  email: "carlos@lab-acme.com.br",
  roles: ["signatory"],
  status: "active",
  teamName: "Qualidade",
  lastLoginUtc: "2026-04-21T17:30:00Z",
  deviceCount: 1,
  competencies: [
    {
      instrumentType: "balanca",
      roleLabel: "Signatario autorizado",
      validUntilUtc: "2026-12-15T00:00:00Z",
    },
  ],
};

const BASE_USERS: DirectoryUserInput[] = [
  ADMIN_USER,
  TECHNICIAN_USER,
  REVIEWER_USER,
  SIGNATORY_USER,
];

const SCENARIOS: UserDirectoryScenario[] = [
  {
    id: "operational-team",
    label: "Equipe operacional",
    description: "Usuarios ativos e competencias autorizadas para seguir com a operacao de V1.",
    ...buildUserDirectoryScenario("2026-04-22T12:00:00Z", [
      ...BASE_USERS,
      {
        userId: "user-invite-1",
        displayName: "Paula Convite",
        email: "paula@lab-acme.com.br",
        roles: ["quality_manager"],
        status: "invited",
        teamName: "Qualidade",
        deviceCount: 0,
        competencies: [],
      },
    ]),
  },
  {
    id: "expiring-competencies",
    label: "Competencias expirando",
    description: "A equipe segue ativa, mas o laboratorio precisa agir antes do vencimento das autorizacoes.",
    ...buildUserDirectoryScenario("2026-04-22T12:00:00Z", [
      ADMIN_USER,
      TECHNICIAN_USER,
      REVIEWER_USER,
      {
        ...SIGNATORY_USER,
        competencies: [
          {
            instrumentType: "balanca",
            roleLabel: "Signatario autorizado",
            validUntilUtc: "2026-05-15T00:00:00Z",
          },
        ],
      },
    ]),
  },
  {
    id: "suspended-access",
    label: "Acesso suspenso e competencia vencida",
    description: "Mostra o estado de atencao quando parte da equipe nao pode mais executar ou assinar.",
    ...buildUserDirectoryScenario("2026-04-22T12:00:00Z", [
      ADMIN_USER,
      TECHNICIAN_USER,
      {
        ...REVIEWER_USER,
        status: "suspended",
        competencies: [
          {
            instrumentType: "balanca",
            roleLabel: "Revisor tecnico",
            validUntilUtc: "2026-03-15T00:00:00Z",
          },
        ],
      },
      SIGNATORY_USER,
    ]),
  },
];

export function listUserDirectoryScenarios(): UserDirectoryScenario[] {
  return SCENARIOS;
}

export function resolveUserDirectoryScenario(scenarioId?: string): UserDirectoryScenario {
  const scenario = SCENARIOS.find((item) => item.id === scenarioId) ?? SCENARIOS[0];

  if (!scenario) {
    throw new Error("missing_user_directory_scenarios");
  }

  return scenario;
}

export function buildUserDirectoryCatalog(scenarioId?: string): UserDirectoryCatalog {
  const selectedScenario = resolveUserDirectoryScenario(scenarioId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listUserDirectoryScenarios(),
  };
}

function buildUserDirectoryScenario(nowUtc: string, users: DirectoryUserInput[]) {
  return buildUserDirectory({
    organizationName: "Lab. Acme",
    nowUtc,
    users,
  });
}

export type UserDirectoryScenarioDefinition = UserDirectoryScenario;
export type UserDirectoryScenarioSelection = UserDirectoryScenarioId;
