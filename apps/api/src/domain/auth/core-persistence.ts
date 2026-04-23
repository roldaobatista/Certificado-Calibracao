import type { CompetencyStatus, MembershipRole, UserLifecycleStatus } from "@afere/contracts";
import { membershipRoleSchema } from "@afere/contracts";
import type { PrismaClient } from "@prisma/client";

export type PersistedCompetencyRecord = {
  instrumentType: string;
  roleLabel: string;
  status: CompetencyStatus;
  validUntilUtc: string;
};

export type PersistedUserRecord = {
  userId: string;
  organizationId: string;
  organizationName: string;
  organizationSlug: string;
  email: string;
  passwordHash: string;
  displayName: string;
  roles: MembershipRole[];
  status: UserLifecycleStatus;
  teamName?: string;
  mfaEnforced: boolean;
  mfaEnrolled: boolean;
  deviceCount: number;
  lastLoginUtc?: string;
  competencies: PersistedCompetencyRecord[];
};

export type PersistedSessionRecord = {
  sessionId: string;
  expiresAtUtc: string;
  user: PersistedUserRecord;
};

export type PersistedOnboardingRecord = {
  organizationId: string;
  organizationName: string;
  organizationSlug: string;
  regulatoryProfile: string;
  normativePackageVersion: string;
  startedAtUtc: string;
  completedAtUtc?: string;
  organizationProfileCompleted: boolean;
  primarySignatoryReady: boolean;
  certificateNumberingConfigured: boolean;
  scopeReviewCompleted: boolean;
  publicQrConfigured: boolean;
};

export type UpdateOnboardingInput = {
  organizationProfileCompleted: boolean;
  primarySignatoryReady: boolean;
  certificateNumberingConfigured: boolean;
  scopeReviewCompleted: boolean;
  publicQrConfigured: boolean;
};

export type BootstrapOrganizationInput = {
  slug: string;
  legalName: string;
  regulatoryProfile: string;
  adminName: string;
  adminEmail: string;
  passwordHash: string;
};

export type CreateSessionInput = {
  organizationId: string;
  userId: string;
  tokenHash: string;
  expiresAt: Date;
};

export interface CorePersistence {
  findUserByEmail(email: string): Promise<PersistedUserRecord | null>;
  findSessionByTokenHash(tokenHash: string): Promise<PersistedSessionRecord | null>;
  createSession(input: CreateSessionInput): Promise<PersistedSessionRecord>;
  revokeSessionByTokenHash(tokenHash: string): Promise<void>;
  touchUserLogin(userId: string, occurredAt: Date): Promise<void>;
  listUsersByOrganization(organizationId: string): Promise<PersistedUserRecord[]>;
  getOnboardingByOrganization(organizationId: string): Promise<PersistedOnboardingRecord | null>;
  updateOnboardingByOrganization(
    organizationId: string,
    input: UpdateOnboardingInput,
  ): Promise<PersistedOnboardingRecord>;
  bootstrapOrganization(input: BootstrapOrganizationInput): Promise<{
    organizationId: string;
    userId: string;
  }>;
}

export function createMemoryCorePersistence(seed: {
  users?: PersistedUserRecord[];
  sessions?: PersistedSessionRecord[];
  onboarding?: PersistedOnboardingRecord[];
} = {}): CorePersistence {
  const users = new Map((seed.users ?? []).map((user) => [user.userId, structuredClone(user)]));
  const sessions = new Map(
    (seed.sessions ?? []).map((session) => [session.sessionId, structuredClone(session)]),
  );
  const tokenHashes = new Map<string, string>();
  const onboarding = new Map(
    (seed.onboarding ?? []).map((record) => [record.organizationId, structuredClone(record)]),
  );

  return {
    async findUserByEmail(email) {
      const normalized = email.trim().toLowerCase();
      return cloneRecord(
        Array.from(users.values()).find((user) => user.email.toLowerCase() === normalized) ?? null,
      );
    },
    async findSessionByTokenHash(tokenHash) {
      const sessionId = tokenHashes.get(tokenHash);
      return cloneRecord(sessionId ? sessions.get(sessionId) ?? null : null);
    },
    async createSession(input) {
      const user = Array.from(users.values()).find((candidate) => candidate.userId === input.userId);
      if (!user) {
        throw new Error("memory_user_not_found");
      }

      const session: PersistedSessionRecord = {
        sessionId: `session-${sessions.size + 1}`,
        expiresAtUtc: input.expiresAt.toISOString(),
        user: cloneRecord(user)!,
      };

      sessions.set(session.sessionId, session);
      tokenHashes.set(input.tokenHash, session.sessionId);
      return cloneRecord(session)!;
    },
    async revokeSessionByTokenHash(tokenHash) {
      const sessionId = tokenHashes.get(tokenHash);
      if (sessionId) {
        sessions.delete(sessionId);
        tokenHashes.delete(tokenHash);
      }
    },
    async touchUserLogin(userId, occurredAt) {
      const user = users.get(userId);
      if (user) {
        user.lastLoginUtc = occurredAt.toISOString();
      }
    },
    async listUsersByOrganization(organizationId) {
      return Array.from(users.values())
        .filter((user) => user.organizationId === organizationId)
        .map((user) => cloneRecord(user)!)
        .sort((left, right) => left.displayName.localeCompare(right.displayName));
    },
    async getOnboardingByOrganization(organizationId) {
      return cloneRecord(onboarding.get(organizationId) ?? null);
    },
    async updateOnboardingByOrganization(organizationId, input) {
      const existing = onboarding.get(organizationId);
      if (!existing) {
        throw new Error("memory_onboarding_not_found");
      }

      const updated: PersistedOnboardingRecord = {
        ...existing,
        ...input,
        completedAtUtc:
          allOnboardingFlagsComplete(input) ? new Date().toISOString() : undefined,
      };
      onboarding.set(organizationId, updated);
      return cloneRecord(updated)!;
    },
    async bootstrapOrganization(input) {
      const organizationId = `memory-org-${onboarding.size + 1}`;
      const userId = `memory-user-${users.size + 1}`;
      const user: PersistedUserRecord = {
        userId,
        organizationId,
        organizationName: input.legalName,
        organizationSlug: input.slug,
        email: input.adminEmail.toLowerCase(),
        passwordHash: input.passwordHash,
        displayName: input.adminName,
        roles: ["admin", "quality_manager"],
        status: "active",
        teamName: "Gestao tecnica",
        mfaEnforced: true,
        mfaEnrolled: true,
        deviceCount: 1,
        competencies: [],
      };
      users.set(userId, user);
      onboarding.set(organizationId, {
        organizationId,
        organizationName: input.legalName,
        organizationSlug: input.slug,
        regulatoryProfile: input.regulatoryProfile,
        normativePackageVersion: "2026-04-20-baseline-v0.1.0",
        startedAtUtc: new Date().toISOString(),
        organizationProfileCompleted: true,
        primarySignatoryReady: false,
        certificateNumberingConfigured: false,
        scopeReviewCompleted: false,
        publicQrConfigured: false,
      });
      return { organizationId, userId };
    },
  };
}

export function createPrismaCorePersistence(prisma: PrismaClient): CorePersistence {
  return {
    async findUserByEmail(email) {
      const user = await prisma.appUser.findUnique({
        where: { email: email.trim().toLowerCase() },
        include: {
          organization: true,
          competencies: true,
        },
      });

      return user ? mapUserRecord(user) : null;
    },
    async findSessionByTokenHash(tokenHash) {
      const session = await prisma.appSession.findUnique({
        where: { tokenHash },
        include: {
          user: {
            include: {
              organization: true,
              competencies: true,
            },
          },
        },
      });

      if (!session || session.revokedAt) {
        return null;
      }

      return {
        sessionId: session.id,
        expiresAtUtc: session.expiresAt.toISOString(),
        user: mapUserRecord(session.user),
      };
    },
    async createSession(input) {
      const session = await prisma.appSession.create({
        data: {
          organizationId: input.organizationId,
          userId: input.userId,
          tokenHash: input.tokenHash,
          expiresAt: input.expiresAt,
        },
        include: {
          user: {
            include: {
              organization: true,
              competencies: true,
            },
          },
        },
      });

      return {
        sessionId: session.id,
        expiresAtUtc: session.expiresAt.toISOString(),
        user: mapUserRecord(session.user),
      };
    },
    async revokeSessionByTokenHash(tokenHash) {
      await prisma.appSession.updateMany({
        where: {
          tokenHash,
          revokedAt: null,
        },
        data: {
          revokedAt: new Date(),
        },
      });
    },
    async touchUserLogin(userId, occurredAt) {
      await prisma.appUser.update({
        where: { id: userId },
        data: {
          lastLoginAt: occurredAt,
        },
      });
    },
    async listUsersByOrganization(organizationId) {
      const users = await prisma.appUser.findMany({
        where: { organizationId },
        include: {
          organization: true,
          competencies: true,
        },
        orderBy: [{ status: "asc" }, { displayName: "asc" }],
      });

      return users.map((user) => mapUserRecord(user));
    },
    async getOnboardingByOrganization(organizationId) {
      const record = await prisma.onboardingState.findUnique({
        where: { organizationId },
        include: { organization: true },
      });

      return record ? mapOnboardingRecord(record) : null;
    },
    async updateOnboardingByOrganization(organizationId, input) {
      const updated = await prisma.onboardingState.upsert({
        where: { organizationId },
        create: {
          organizationId,
          startedAt: new Date(),
          completedAt: allOnboardingFlagsComplete(input) ? new Date() : null,
          ...input,
        },
        update: {
          ...input,
          completedAt: allOnboardingFlagsComplete(input) ? new Date() : null,
        },
        include: { organization: true },
      });

      return mapOnboardingRecord(updated);
    },
    async bootstrapOrganization(input) {
      const created = await prisma.$transaction(async (tx) => {
        const organization = await tx.organization.create({
          data: {
            slug: input.slug.trim().toLowerCase(),
            legalName: input.legalName.trim(),
            regulatoryProfile: input.regulatoryProfile.trim(),
            normativePackageVersion: "2026-04-20-baseline-v0.1.0",
          },
        });

        const user = await tx.appUser.create({
          data: {
            organizationId: organization.id,
            email: input.adminEmail.trim().toLowerCase(),
            passwordHash: input.passwordHash,
            displayName: input.adminName.trim(),
            roles: ["admin", "quality_manager"],
            status: "active",
            teamName: "Gestao tecnica",
            mfaEnforced: true,
            mfaEnrolled: true,
            deviceCount: 1,
          },
        });

        await tx.onboardingState.create({
          data: {
            organizationId: organization.id,
            startedAt: new Date(),
            organizationProfileCompleted: true,
            primarySignatoryReady: false,
            certificateNumberingConfigured: false,
            scopeReviewCompleted: false,
            publicQrConfigured: false,
          },
        });

        return {
          organizationId: organization.id,
          userId: user.id,
        };
      });

      return created;
    },
  };
}

function mapUserRecord(
  user: {
    id: string;
    organizationId: string;
    email: string;
    passwordHash: string;
    displayName: string;
    roles: string[];
    status: string;
    teamName: string | null;
    mfaEnforced: boolean;
    mfaEnrolled: boolean;
    deviceCount: number;
    lastLoginAt: Date | null;
    organization: {
      id: string;
      legalName: string;
      slug: string;
    };
    competencies: Array<{
      instrumentType: string;
      roleLabel: string;
      status: string;
      validUntil: Date;
    }>;
  },
): PersistedUserRecord {
  return {
    userId: user.id,
    organizationId: user.organization.id,
    organizationName: user.organization.legalName,
    organizationSlug: user.organization.slug,
    email: user.email,
    passwordHash: user.passwordHash,
    displayName: user.displayName,
    roles: parseRoles(user.roles),
    status: parseLifecycleStatus(user.status),
    teamName: user.teamName ?? undefined,
    mfaEnforced: user.mfaEnforced,
    mfaEnrolled: user.mfaEnrolled,
    deviceCount: user.deviceCount,
    lastLoginUtc: user.lastLoginAt?.toISOString(),
    competencies: user.competencies.map((competency) => ({
      instrumentType: competency.instrumentType,
      roleLabel: competency.roleLabel,
      status: parseCompetencyStatus(competency.status),
      validUntilUtc: competency.validUntil.toISOString(),
    })),
  };
}

function mapOnboardingRecord(
  record: {
    organizationId: string;
    startedAt: Date;
    completedAt: Date | null;
    organizationProfileCompleted: boolean;
    primarySignatoryReady: boolean;
    certificateNumberingConfigured: boolean;
    scopeReviewCompleted: boolean;
    publicQrConfigured: boolean;
    organization: {
      legalName: string;
      slug: string;
      regulatoryProfile: string;
      normativePackageVersion: string;
    };
  },
): PersistedOnboardingRecord {
  return {
    organizationId: record.organizationId,
    organizationName: record.organization.legalName,
    organizationSlug: record.organization.slug,
    regulatoryProfile: record.organization.regulatoryProfile,
    normativePackageVersion: record.organization.normativePackageVersion,
    startedAtUtc: record.startedAt.toISOString(),
    completedAtUtc: record.completedAt?.toISOString(),
    organizationProfileCompleted: record.organizationProfileCompleted,
    primarySignatoryReady: record.primarySignatoryReady,
    certificateNumberingConfigured: record.certificateNumberingConfigured,
    scopeReviewCompleted: record.scopeReviewCompleted,
    publicQrConfigured: record.publicQrConfigured,
  };
}

function parseRoles(values: string[]): MembershipRole[] {
  const roles = values
    .map((value) => membershipRoleSchema.safeParse(value))
    .filter((result): result is { success: true; data: MembershipRole } => result.success)
    .map((result) => result.data);

  return roles.length > 0 ? roles : ["auditor_readonly"];
}

function parseLifecycleStatus(value: string): UserLifecycleStatus {
  if (value === "invited" || value === "suspended") {
    return value;
  }

  return "active";
}

function parseCompetencyStatus(value: string): CompetencyStatus {
  if (value === "expired" || value === "expiring") {
    return value;
  }

  return "authorized";
}

function allOnboardingFlagsComplete(input: UpdateOnboardingInput) {
  return (
    input.organizationProfileCompleted &&
    input.primarySignatoryReady &&
    input.certificateNumberingConfigured &&
    input.scopeReviewCompleted &&
    input.publicQrConfigured
  );
}

function cloneRecord<T>(value: T): T {
  return structuredClone(value);
}
