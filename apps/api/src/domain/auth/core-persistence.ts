import { randomUUID } from "node:crypto";

import type { CompetencyStatus, MembershipRole, UserLifecycleStatus } from "@afere/contracts";
import { membershipRoleSchema } from "@afere/contracts";
import { withTenant } from "@afere/db";
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
  authLevel: "full" | "partial";
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
  authLevel?: "full" | "partial";
};

export type SaveUserInput = {
  organizationId: string;
  userId?: string;
  actorUserId?: string;
  email: string;
  passwordHash?: string;
  displayName: string;
  roles: MembershipRole[];
  status: UserLifecycleStatus;
  teamName?: string;
  mfaEnforced: boolean;
  mfaEnrolled: boolean;
  deviceCount: number;
  competencies: Array<{
    instrumentType: string;
    roleLabel: string;
    validUntil: Date;
  }>;
};

export interface CorePersistence {
  findUserByEmail(email: string): Promise<PersistedUserRecord | null>;
  findSessionByTokenHash(tokenHash: string): Promise<PersistedSessionRecord | null>;
  createSession(input: CreateSessionInput): Promise<PersistedSessionRecord>;
  promoteSessionToFull(tokenHash: string): Promise<void>;
  revokeSessionByTokenHash(tokenHash: string): Promise<void>;
  revokeSessionsByUserId(userId: string): Promise<void>;
  touchUserLogin(userId: string, occurredAt: Date): Promise<void>;
  listUsersByOrganization(organizationId: string): Promise<PersistedUserRecord[]>;
  saveUser(input: SaveUserInput): Promise<PersistedUserRecord>;
  setUserStatus(
    organizationId: string,
    userId: string,
    status: UserLifecycleStatus,
    actorUserId?: string,
  ): Promise<void>;
  getOnboardingByOrganization(organizationId: string): Promise<PersistedOnboardingRecord | null>;
  updateOnboardingByOrganization(
    organizationId: string,
    input: UpdateOnboardingInput,
  ): Promise<PersistedOnboardingRecord>;
  bootstrapOrganization(input: BootstrapOrganizationInput): Promise<{
    organizationId: string;
    userId: string;
  }>;
  hasAnyOrganization(): Promise<boolean>;
  // MFA
  findMfaCredentialByUserId(userId: string): Promise<{ secret: string } | null>;
  createMfaCredential(userId: string, secret: string): Promise<void>;
  markMfaVerified(userId: string): Promise<void>;
  generateRecoveryCodes(userId: string, codeHashes: string[]): Promise<void>;
  useRecoveryCode(userId: string, codeHash: string): Promise<boolean>;
}

export function createMemoryCorePersistence(seed: {
  users?: PersistedUserRecord[];
  sessions?: PersistedSessionRecord[];
  onboarding?: PersistedOnboardingRecord[];
  mfaCredentials?: Array<{ userId: string; secret: string }>;
} = {}): CorePersistence {
  const users = new Map((seed.users ?? []).map((user) => [user.userId, structuredClone(user)]));
  const sessions = new Map(
    (seed.sessions ?? []).map((session) => [session.sessionId, structuredClone(session)]),
  );
  const tokenHashes = new Map<string, string>();
  const onboarding = new Map(
    (seed.onboarding ?? []).map((record) => [record.organizationId, structuredClone(record)]),
  );

  const mfaCredentials = new Map<string, { secret: string }>(
    (seed.mfaCredentials ?? []).map((cred) => [cred.userId, { secret: cred.secret }]),
  );
  const recoveryCodes = new Map<string, Array<{ codeHash: string; usedAt?: Date }>>();
  let sessionCounter = sessions.size + 1;

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
        sessionId: `session-${sessionCounter++}`,
        expiresAtUtc: input.expiresAt.toISOString(),
        authLevel: input.authLevel ?? "full",
        user: cloneRecord(user)!,
      };

      sessions.set(session.sessionId, session);
      tokenHashes.set(input.tokenHash, session.sessionId);
      return cloneRecord(session)!;
    },
    async promoteSessionToFull(tokenHash) {
      const sessionId = tokenHashes.get(tokenHash);
      const session = sessionId ? sessions.get(sessionId) : undefined;
      if (session) {
        session.authLevel = "full";
      }
    },
    async revokeSessionByTokenHash(tokenHash) {
      const sessionId = tokenHashes.get(tokenHash);
      if (sessionId) {
        sessions.delete(sessionId);
        tokenHashes.delete(tokenHash);
      }
    },
    async revokeSessionsByUserId(userId) {
      for (const [sessionId, session] of sessions.entries()) {
        if (session.user.userId === userId) {
          for (const [hash, sid] of tokenHashes.entries()) {
            if (sid === sessionId) {
              tokenHashes.delete(hash);
            }
          }
          sessions.delete(sessionId);
        }
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
    async saveUser(input) {
      const existing = input.userId ? users.get(input.userId) : null;
      const userId = input.userId ?? `memory-user-${users.size + 1}`;
      const passwordHash =
        input.passwordHash ?? existing?.passwordHash ?? (() => {
          throw new Error("memory_password_hash_required");
        })();

      const user: PersistedUserRecord = {
        userId,
        organizationId: input.organizationId,
        organizationName: existing?.organizationName ?? "Laboratorio Persistido",
        organizationSlug: existing?.organizationSlug ?? "lab-persistido",
        email: input.email.trim().toLowerCase(),
        passwordHash,
        displayName: input.displayName,
        roles: input.roles,
        status: input.status,
        teamName: input.teamName,
        mfaEnforced: input.mfaEnforced,
        mfaEnrolled: input.mfaEnrolled,
        deviceCount: input.deviceCount,
        lastLoginUtc: existing?.lastLoginUtc,
        competencies: input.competencies.map((competency) => ({
          instrumentType: competency.instrumentType,
          roleLabel: competency.roleLabel,
          status: inferCompetencyStatus(competency.validUntil),
          validUntilUtc: competency.validUntil.toISOString(),
        })),
      };

      users.set(userId, user);
      return cloneRecord(user)!;
    },
    async setUserStatus(organizationId, userId, status) {
      const existing = users.get(userId);
      if (!existing || existing.organizationId !== organizationId) {
        throw new Error("memory_user_not_found");
      }

      users.set(userId, {
        ...existing,
        status,
      });
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
    async hasAnyOrganization() {
      return onboarding.size > 0;
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
      // Seed MFA credential para testes
      mfaCredentials.set(userId, { secret: "JBSWY3DPEHPK3PXP" });
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
    async findMfaCredentialByUserId(userId) {
      return cloneRecord(mfaCredentials.get(userId) ?? null);
    },
    async createMfaCredential(userId, secret) {
      mfaCredentials.set(userId, { secret });
    },
    async markMfaVerified(userId) {
      const user = users.get(userId);
      if (user) {
        user.mfaEnrolled = true;
      }
    },
    async generateRecoveryCodes(userId, codeHashes) {
      recoveryCodes.set(userId, codeHashes.map((codeHash) => ({ codeHash })));
    },
    async useRecoveryCode(userId, codeHash) {
      const codes = recoveryCodes.get(userId);
      if (!codes) return false;
      const entry = codes.find((c) => c.codeHash === codeHash && !c.usedAt);
      if (!entry) return false;
      entry.usedAt = new Date();
      return true;
    },
  };
}

export function createPrismaCorePersistence(
  prismaAuth: PrismaClient,
  prismaApp?: PrismaClient,
): CorePersistence {
  const prisma = prismaApp ?? prismaAuth;
  return {
    async findUserByEmail(email) {
      const user = await prismaAuth.appUser.findUnique({
        where: { email: email.trim().toLowerCase() },
        include: {
          organization: true,
          competencies: true,
        },
      });

      return user ? mapUserRecord(user) : null;
    },
    async findSessionByTokenHash(tokenHash) {
      const session = await prismaAuth.appSession.findUnique({
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
        authLevel: session.authLevel === "partial" ? "partial" : "full",
        user: mapUserRecord(session.user),
      };
    },
    async createSession(input) {
      const session = await prismaAuth.appSession.create({
        data: {
          organizationId: input.organizationId,
          userId: input.userId,
          tokenHash: input.tokenHash,
          expiresAt: input.expiresAt,
          authLevel: input.authLevel ?? "full",
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
        authLevel: session.authLevel === "partial" ? "partial" : "full",
        user: mapUserRecord(session.user),
      };
    },
    async promoteSessionToFull(tokenHash) {
      await prismaAuth.appSession.updateMany({
        where: { tokenHash, revokedAt: null },
        data: { authLevel: "full" },
      });
    },
    async revokeSessionByTokenHash(tokenHash) {
      await prismaAuth.appSession.updateMany({
        where: {
          tokenHash,
          revokedAt: null,
        },
        data: {
          revokedAt: new Date(),
        },
      });
    },
    async revokeSessionsByUserId(userId) {
      await prismaAuth.appSession.updateMany({
        where: {
          userId,
          revokedAt: null,
        },
        data: {
          revokedAt: new Date(),
        },
      });
    },
    async touchUserLogin(userId, occurredAt) {
      await prismaAuth.appUser.update({
        where: { id: userId },
        data: {
          lastLoginAt: occurredAt,
        },
      });
    },
    async listUsersByOrganization(organizationId) {
      const users = await withTenant(prisma, organizationId, async (tx) => {
        return tx.appUser.findMany({
          where: { organizationId },
          include: {
            organization: true,
            competencies: true,
          },
          orderBy: [{ status: "asc" }, { displayName: "asc" }],
        });
      });

      return users.map((user) => mapUserRecord(user));
    },
    async saveUser(input) {
      const saved = await withTenant(prisma, input.organizationId, async (tx) => {
        const existing = input.userId
          ? await tx.appUser.findUnique({
              where: { id: input.userId },
              include: {
                organization: true,
                competencies: true,
              },
            })
          : null;

        const user = input.userId
          ? await tx.appUser.update({
              where: { id: input.userId },
              data: {
                email: input.email.trim().toLowerCase(),
                passwordHash: input.passwordHash ?? existing?.passwordHash,
                displayName: input.displayName.trim(),
                roles: input.roles,
                status: input.status,
                teamName: input.teamName?.trim() || null,
                mfaEnforced: input.mfaEnforced,
                mfaEnrolled: input.mfaEnrolled,
                deviceCount: input.deviceCount,
              },
              include: {
                organization: true,
                competencies: true,
              },
            })
          : await tx.appUser.create({
              data: {
                organizationId: input.organizationId,
                email: input.email.trim().toLowerCase(),
                passwordHash:
                  input.passwordHash ?? (() => {
                    throw new Error("password_hash_required");
                  })(),
                displayName: input.displayName.trim(),
                roles: input.roles,
                status: input.status,
                teamName: input.teamName?.trim() || null,
                mfaEnforced: input.mfaEnforced,
                mfaEnrolled: input.mfaEnrolled,
                deviceCount: input.deviceCount,
              },
              include: {
                organization: true,
                competencies: true,
              },
            });

        await tx.userCompetency.deleteMany({
          where: {
            organizationId: input.organizationId,
            userId: user.id,
          },
        });

        if (input.competencies.length > 0) {
          await tx.userCompetency.createMany({
            data: input.competencies.map((competency) => ({
              id: randomUUID(),
              organizationId: input.organizationId,
              userId: user.id,
              instrumentType: competency.instrumentType.trim(),
              roleLabel: competency.roleLabel.trim(),
              status: inferCompetencyStatus(competency.validUntil),
              validUntil: competency.validUntil,
            })),
          });
        }

        await tx.registryAuditEvent.create({
          data: {
            organizationId: input.organizationId,
            entityType: "user",
            entityId: user.id,
            action: input.userId ? "update" : "create",
            actorUserId: input.actorUserId,
            summary: input.userId
              ? `Usuario ${input.displayName.trim()} atualizado.`
              : `Usuario ${input.displayName.trim()} cadastrado.`,
          },
        });

        return tx.appUser.findUniqueOrThrow({
          where: { id: user.id },
          include: {
            organization: true,
            competencies: true,
          },
        });
      });

      return mapUserRecord(saved);
    },
    async setUserStatus(organizationId, userId, status, actorUserId) {
      const updated = await withTenant(prisma, organizationId, async (tx) => {
        const user = await tx.appUser.update({
          where: { id: userId },
          data: { status },
        });

        await tx.registryAuditEvent.create({
          data: {
            organizationId,
            entityType: "user",
            entityId: userId,
            action: status === "suspended" ? "archive" : "update",
            actorUserId,
            summary:
              status === "suspended"
                ? `Usuario ${user.displayName} suspenso.`
                : `Status do usuario ${user.displayName} alterado para ${status}.`,
          },
        });

        return user;
      });
    },
    async getOnboardingByOrganization(organizationId) {
      const record = await withTenant(prisma, organizationId, async (tx) => {
        return tx.onboardingState.findUnique({
          where: { organizationId },
          include: { organization: true },
        });
      });

      return record ? mapOnboardingRecord(record) : null;
    },
    async updateOnboardingByOrganization(organizationId, input) {
      const updated = await withTenant(prisma, organizationId, async (tx) => {
        return tx.onboardingState.upsert({
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
      });

      return mapOnboardingRecord(updated);
    },
    async hasAnyOrganization() {
      const count = await prismaAuth.organization.count();
      return count > 0;
    },
    async bootstrapOrganization(input) {
      const created = await prismaAuth.$transaction(async (tx) => {
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

        await tx.mfaCredential.create({
          data: {
            userId: user.id,
            type: "totp",
            secret: "JBSWY3DPEHPK3PXP",
            verified: true,
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
    async findMfaCredentialByUserId(userId) {
      const cred = await prismaAuth.mfaCredential.findFirst({
        where: { userId, verified: true },
      });
      return cred ? { secret: cred.secret } : null;
    },
    async createMfaCredential(userId, secret) {
      await prismaAuth.mfaCredential.create({
        data: { userId, type: "totp", secret, verified: false },
      });
    },
    async markMfaVerified(userId) {
      await prismaAuth.$transaction(async (tx) => {
        await tx.mfaCredential.updateMany({
          where: { userId },
          data: { verified: true },
        });
        await tx.appUser.update({
          where: { id: userId },
          data: { mfaEnrolled: true },
        });
      });
    },
    async generateRecoveryCodes(userId, codeHashes) {
      await prismaAuth.mfaRecoveryCode.createMany({
        data: codeHashes.map((codeHash) => ({ userId, codeHash })),
      });
    },
    async useRecoveryCode(userId, codeHash) {
      const result = await prismaAuth.mfaRecoveryCode.updateMany({
        where: { userId, codeHash, usedAt: null },
        data: { usedAt: new Date() },
      });
      return result.count > 0;
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

function inferCompetencyStatus(validUntil: Date): CompetencyStatus {
  const remainingMs = validUntil.getTime() - Date.now();
  if (remainingMs < 0) {
    return "expired";
  }

  return remainingMs <= 90 * 24 * 60 * 60 * 1000 ? "expiring" : "authorized";
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
