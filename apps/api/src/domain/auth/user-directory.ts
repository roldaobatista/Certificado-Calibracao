import type {
  CompetencyStatus,
  DirectoryUser,
  MembershipRole,
  UserCompetency,
  UserDirectorySummary,
  UserLifecycleStatus,
} from "@afere/contracts";

const EXPIRING_WINDOW_DAYS = 90;
const EXPIRING_WINDOW_MS = EXPIRING_WINDOW_DAYS * 24 * 60 * 60 * 1000;

export interface DirectoryCompetencyInput {
  instrumentType: string;
  roleLabel: string;
  validUntilUtc: string;
}

export interface DirectoryUserInput {
  userId: string;
  displayName: string;
  email: string;
  roles: MembershipRole[];
  status: UserLifecycleStatus;
  teamName?: string;
  lastLoginUtc?: string;
  deviceCount: number;
  competencies: DirectoryCompetencyInput[];
}

export interface BuildUserDirectoryInput {
  organizationName: string;
  nowUtc: string;
  users: DirectoryUserInput[];
}

export function buildUserDirectory(input: BuildUserDirectoryInput): {
  summary: UserDirectorySummary;
  users: DirectoryUser[];
} {
  const users = input.users.map((user) => ({
    userId: user.userId,
    displayName: user.displayName,
    email: user.email,
    roles: user.roles,
    status: user.status,
    teamName: user.teamName,
    lastLoginUtc: user.lastLoginUtc,
    deviceCount: user.deviceCount,
    competencies: user.competencies.map((competency) =>
      classifyCompetency(competency, input.nowUtc),
    ),
  }));

  const summary = buildSummary(input.organizationName, users);

  return {
    summary,
    users,
  };
}

export function classifyCompetency(
  input: DirectoryCompetencyInput,
  nowUtc: string,
): UserCompetency {
  const now = Date.parse(nowUtc);
  const validUntil = Date.parse(input.validUntilUtc);

  let status: CompetencyStatus = "expired";
  if (Number.isFinite(now) && Number.isFinite(validUntil)) {
    const remainingMs = validUntil - now;
    status =
      remainingMs < 0 ? "expired" : remainingMs <= EXPIRING_WINDOW_MS ? "expiring" : "authorized";
  }

  return {
    instrumentType: input.instrumentType,
    roleLabel: input.roleLabel,
    validUntilUtc: input.validUntilUtc,
    status,
  };
}

function buildSummary(
  organizationName: string,
  users: DirectoryUser[],
): UserDirectorySummary {
  let activeUsers = 0;
  let invitedUsers = 0;
  let suspendedUsers = 0;
  let expiringCompetencies = 0;
  let expiredCompetencies = 0;

  for (const user of users) {
    if (user.status === "active") activeUsers += 1;
    if (user.status === "invited") invitedUsers += 1;
    if (user.status === "suspended") suspendedUsers += 1;

    for (const competency of user.competencies) {
      if (competency.status === "expiring") expiringCompetencies += 1;
      if (competency.status === "expired") expiredCompetencies += 1;
    }
  }

  return {
    status:
      suspendedUsers > 0 || expiredCompetencies > 0 || expiringCompetencies > 0
        ? "attention"
        : "ready",
    organizationName,
    activeUsers,
    invitedUsers,
    suspendedUsers,
    expiringCompetencies,
    expiredCompetencies,
  };
}
