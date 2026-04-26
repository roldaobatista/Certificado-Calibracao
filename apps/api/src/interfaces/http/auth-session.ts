import { createHash, randomBytes } from "node:crypto";

import {
  authLoginResponseSchema,
  authSessionSchema,
  mfaEnrollResponseSchema,
  mfaVerifyBodySchema,
  mfaConfirmEnrollBodySchema,
  mfaRecoverBodySchema,
  type AuthLoginResponse,
  type AuthSession,
  type MembershipRole,
} from "@afere/contracts";
import type { FastifyInstance } from "fastify";
import { z } from "zod";

import type { CorePersistence } from "../../domain/auth/core-persistence.js";
import { hashPassword, verifyPassword } from "../../domain/auth/password.js";
import {
  clearSessionCookie,
  createSessionExpiry,
  createSessionToken,
  hashSessionToken,
  hasPrivilegedRole,
  issueSessionCookie,
  requireAuthenticatedRequest,
  resolveAuthenticatedRequest,
  toAuthSession,
} from "../../domain/auth/session-auth.js";
import { generateTotpSecret, verifyTotp, generateTotpUri } from "../../domain/auth/totp.js";
import type { Env } from "../../config/env.js";

const LoginBodySchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  redirectTo: z.string().min(1).optional(),
});

const BootstrapBodySchema = z.object({
  slug: z.string().min(3).max(64),
  legalName: z.string().min(3).max(160),
  regulatoryProfile: z.string().min(3).max(32).default("type_b"),
  adminName: z.string().min(3).max(140),
  adminEmail: z.string().email(),
  password: z.string().min(8),
  redirectTo: z.string().min(1).optional(),
});

import { isRedirectAllowed } from "./redirect-helpers.js";

export const ONBOARDING_ALLOWED_ROLES: MembershipRole[] = ["admin", "quality_manager"];
export const USER_DIRECTORY_ALLOWED_ROLES: MembershipRole[] = ["admin", "quality_manager"];
export const REGISTRY_ALLOWED_ROLES: MembershipRole[] = [
  "admin",
  "quality_manager",
  "signatory",
  "technical_reviewer",
  "technician",
];
export const REGISTRY_WRITE_ALLOWED_ROLES: MembershipRole[] = ["admin", "quality_manager"];
export const WORKSPACE_ALLOWED_ROLES: MembershipRole[] = [
  "admin",
  "quality_manager",
  "signatory",
  "technical_reviewer",
  "technician",
];
export const PORTAL_ALLOWED_ROLES: MembershipRole[] = ["external_client"];
export const SERVICE_ORDER_WRITE_ALLOWED_ROLES: MembershipRole[] = [
  "admin",
  "quality_manager",
  "signatory",
  "technical_reviewer",
  "technician",
];
export const QUALITY_ALLOWED_ROLES: MembershipRole[] = [
  "admin",
  "quality_manager",
  "signatory",
  "technical_reviewer",
];
export const QUALITY_WRITE_ALLOWED_ROLES: MembershipRole[] = ["admin", "quality_manager"];
export const SETTINGS_ALLOWED_ROLES: MembershipRole[] = QUALITY_ALLOWED_ROLES;
export const SETTINGS_WRITE_ALLOWED_ROLES: MembershipRole[] = QUALITY_WRITE_ALLOWED_ROLES;

export async function registerAuthSessionRoutes(
  app: FastifyInstance,
  persistence: CorePersistence,
  env: Env,
) {
  const cookieOpts = {
    secure: env.NODE_ENV === "production",
    sameSite: "Strict" as const,
  };
  const redirectAllowlist = env.REDIRECT_ALLOWLIST;
  app.get("/auth/session", async (request, reply) => {
    const session = await resolveAuthenticatedRequest(request, persistence);
    const payload: AuthSession = session ? toAuthSession(session) : { authenticated: false };
    // Gerar token CSRF para requests mutáveis subsequentes
    const csrfToken = reply.generateCsrf();
    reply.header("X-CSRF-Token", csrfToken);
    return reply.code(200).send(authSessionSchema.parse(payload));
  });

  app.post("/auth/login", {
    config: { rateLimit: { max: 5, timeWindow: 15 * 60 * 1000 } },
    handler: async (request, reply) => {
    const body = LoginBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    const user = await persistence.findUserByEmail(body.data.email);
    if (!user || !verifyPassword(body.data.password, user.passwordHash)) {
      const payload: AuthLoginResponse = { ok: false, reason: "invalid_credentials" };
      return reply.code(401).send(authLoginResponseSchema.parse(payload));
    }

    if (user.status !== "active") {
      const payload: AuthLoginResponse = { ok: false, reason: "inactive_user" };
      return reply.code(403).send(authLoginResponseSchema.parse(payload));
    }

    if (hasPrivilegedRole(user.roles) && !user.mfaEnrolled) {
      const payload: AuthLoginResponse = { ok: false, reason: "mfa_required" };
      return reply.code(403).send(authLoginResponseSchema.parse(payload));
    }

    // Rotação de sessão: invalidar sessões anteriores do mesmo usuário
    await persistence.revokeSessionsByUserId(user.userId);

    const token = createSessionToken();
    const isMfaRequired = user.mfaEnrolled;
    const expiresAt = isMfaRequired
      ? new Date(Date.now() + 5 * 60 * 1000) // 5 min para sessão parcial
      : createSessionExpiry(user.roles, env.NODE_ENV);
    const session = await persistence.createSession({
      organizationId: user.organizationId,
      userId: user.userId,
      tokenHash: hashSessionToken(token),
      expiresAt,
      authLevel: isMfaRequired ? "partial" : "full",
    });

    await persistence.touchUserLogin(user.userId, new Date());
    issueSessionCookie(reply, token, expiresAt, cookieOpts);

    if (isMfaRequired) {
      const payload: AuthLoginResponse = { ok: false, reason: "mfa_challenge" };
      return reply.code(403).send(authLoginResponseSchema.parse(payload));
    }

    const payload: AuthLoginResponse = {
      ok: true,
      session: toAuthSession(session),
    };

    if (body.data.redirectTo && isRedirectAllowed(body.data.redirectTo, redirectAllowlist)) {
      return reply.redirect(body.data.redirectTo);
    }

    return reply.code(200).send(authLoginResponseSchema.parse(payload));
    },
  });

  app.post("/auth/logout", {
    config: { rateLimit: { max: 20, timeWindow: 60 * 1000 } },
    handler: async (request, reply) => {
    const session = await resolveAuthenticatedRequest(request, persistence);
    if (session) {
      await persistence.revokeSessionByTokenHash(session.tokenHash);
    }

    clearSessionCookie(reply, cookieOpts);
    const redirectTo = readRedirectTarget(request.body);

    if (redirectTo && isRedirectAllowed(redirectTo, redirectAllowlist)) {
      return reply.redirect(redirectTo);
    }

    return reply.code(204).send();
    },
  });

  app.post("/auth/mfa/verify", {
    config: { rateLimit: { max: 5, timeWindow: 60 * 1000 } },
    handler: async (request, reply) => {
      const session = await resolveAuthenticatedRequest(request, persistence);
      if (!session || session.authLevel !== "partial") {
        return reply.code(401).send({ error: "authentication_required" });
      }

      const body = mfaVerifyBodySchema.safeParse(request.body);
      if (!body.success) {
        return reply.code(400).send({ error: "invalid_body" });
      }

      const cred = await persistence.findMfaCredentialByUserId(session.user.userId);
      if (!cred) {
        return reply.code(403).send({ error: "mfa_not_configured" });
      }

      if (!verifyTotp(cred.secret, body.data.code)) {
        return reply.code(403).send({ error: "invalid_mfa_code" });
      }

      await persistence.promoteSessionToFull(session.tokenHash);

      const newExpiry = createSessionExpiry(session.user.roles, env.NODE_ENV);
      // Atualizar cookie com nova expiração
      const newToken = createSessionToken();
      const newSession = await persistence.createSession({
        organizationId: session.user.organizationId,
        userId: session.user.userId,
        tokenHash: hashSessionToken(newToken),
        expiresAt: newExpiry,
        authLevel: "full",
      });
      await persistence.revokeSessionByTokenHash(session.tokenHash);
      issueSessionCookie(reply, newToken, newExpiry, cookieOpts);

      return reply.code(200).send(authLoginResponseSchema.parse({
        ok: true,
        session: toAuthSession(newSession),
      }));
    },
  });

  app.post("/auth/mfa/recover", {
    config: { rateLimit: { max: 3, timeWindow: 60 * 60 * 1000 } },
    handler: async (request, reply) => {
      const session = await resolveAuthenticatedRequest(request, persistence);
      if (!session || session.authLevel !== "partial") {
        return reply.code(401).send({ error: "authentication_required" });
      }

      const body = mfaRecoverBodySchema.safeParse(request.body);
      if (!body.success) {
        return reply.code(400).send({ error: "invalid_body" });
      }

      const codeHash = createHash("sha256").update(body.data.code).digest("hex");
      const ok = await persistence.useRecoveryCode(session.user.userId, codeHash);
      if (!ok) {
        return reply.code(403).send({ error: "invalid_recovery_code" });
      }

      const newExpiry = createSessionExpiry(session.user.roles, env.NODE_ENV);
      const newToken = createSessionToken();
      const newSession = await persistence.createSession({
        organizationId: session.user.organizationId,
        userId: session.user.userId,
        tokenHash: hashSessionToken(newToken),
        expiresAt: newExpiry,
        authLevel: "full",
      });
      await persistence.revokeSessionByTokenHash(session.tokenHash);
      issueSessionCookie(reply, newToken, newExpiry, cookieOpts);

      return reply.code(200).send(authLoginResponseSchema.parse({
        ok: true,
        session: toAuthSession(newSession),
      }));
    },
  });

  app.post("/auth/mfa/enroll", {
    config: { rateLimit: { max: 5, timeWindow: 60 * 60 * 1000 } },
    handler: async (request, reply) => {
      const context = await requireAuthenticatedRequest(request, reply, persistence, undefined, "partial");
      if (!context) return;

      const secret = generateTotpSecret();
      await persistence.createMfaCredential(context.user.userId, secret.base32);

      return reply.code(200).send(mfaEnrollResponseSchema.parse({
        secret: secret.base32,
        uri: generateTotpUri(secret.base32, context.user.email, "Aferê"),
      }));
    },
  });

  app.post("/auth/mfa/confirm-enrollment", {
    config: { rateLimit: { max: 5, timeWindow: 60 * 60 * 1000 } },
    handler: async (request, reply) => {
      const context = await requireAuthenticatedRequest(request, reply, persistence, undefined, "partial");
      if (!context) return;

      const body = mfaConfirmEnrollBodySchema.safeParse(request.body);
      if (!body.success) {
        return reply.code(400).send({ error: "invalid_body" });
      }

      const cred = await persistence.findMfaCredentialByUserId(context.user.userId);
      if (!cred) {
        return reply.code(400).send({ error: "enrollment_not_started" });
      }

      if (!verifyTotp(cred.secret, body.data.code)) {
        return reply.code(403).send({ error: "invalid_mfa_code" });
      }

      await persistence.markMfaVerified(context.user.userId);

      // Gerar recovery codes
      const codes: string[] = [];
      const codeHashes: string[] = [];
      for (let i = 0; i < 8; i++) {
        const code = randomBytes(4).toString("hex").toUpperCase();
        codes.push(code);
        codeHashes.push(createHash("sha256").update(code).digest("hex"));
      }
      await persistence.generateRecoveryCodes(context.user.userId, codeHashes);

      return reply.code(200).send({ ok: true, recoveryCodes: codes });
    },
  });

  app.post("/onboarding/bootstrap", {
    config: { rateLimit: { max: 3, timeWindow: 60 * 60 * 1000 } },
    handler: async (request, reply) => {
    const body = BootstrapBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
    }

    // Proteger bootstrap: exigir flag explícita e impedir reexecução
    if (!env.BOOTSTRAP_ENABLED) {
      return reply.code(403).send({ error: "bootstrap_disabled" });
    }

    const anyOrg = await persistence.hasAnyOrganization();
    if (anyOrg) {
      return reply.code(403).send({ error: "bootstrap_already_completed" });
    }

    try {
      await persistence.bootstrapOrganization({
        slug: body.data.slug,
        legalName: body.data.legalName,
        regulatoryProfile: body.data.regulatoryProfile,
        adminName: body.data.adminName,
        adminEmail: body.data.adminEmail,
        passwordHash: hashPassword(body.data.password, randomBytes(16).toString("base64url")),
      });
    } catch (error) {
      if (isConflictError(error)) {
        return reply.code(409).send({ error: "bootstrap_conflict" });
      }

      throw error;
    }

    const fallbackRedirect = env.NODE_ENV === "production"
      ? "/auth/login?created=1"
      : "http://127.0.0.1:3002/auth/login?created=1";
    const target = body.data.redirectTo && isRedirectAllowed(body.data.redirectTo, redirectAllowlist)
      ? body.data.redirectTo
      : fallbackRedirect;

    return reply.redirect(target);
    },
  });
}

export async function requireOnboardingAccess(
  request: Parameters<typeof requireAuthenticatedRequest>[0],
  reply: Parameters<typeof requireAuthenticatedRequest>[1],
  persistence: CorePersistence,
) {
  return requireAuthenticatedRequest(request, reply, persistence, ONBOARDING_ALLOWED_ROLES);
}

export async function requireUserDirectoryAccess(
  request: Parameters<typeof requireAuthenticatedRequest>[0],
  reply: Parameters<typeof requireAuthenticatedRequest>[1],
  persistence: CorePersistence,
) {
  return requireAuthenticatedRequest(request, reply, persistence, USER_DIRECTORY_ALLOWED_ROLES);
}

export async function requireWorkspaceAccess(
  request: Parameters<typeof requireAuthenticatedRequest>[0],
  reply: Parameters<typeof requireAuthenticatedRequest>[1],
  persistence: CorePersistence,
) {
  return requireAuthenticatedRequest(request, reply, persistence, WORKSPACE_ALLOWED_ROLES);
}

export async function requirePortalAccess(
  request: Parameters<typeof requireAuthenticatedRequest>[0],
  reply: Parameters<typeof requireAuthenticatedRequest>[1],
  persistence: CorePersistence,
) {
  return requireAuthenticatedRequest(request, reply, persistence, PORTAL_ALLOWED_ROLES);
}

export async function requireServiceOrderWriteAccess(
  request: Parameters<typeof requireAuthenticatedRequest>[0],
  reply: Parameters<typeof requireAuthenticatedRequest>[1],
  persistence: CorePersistence,
) {
  return requireAuthenticatedRequest(request, reply, persistence, SERVICE_ORDER_WRITE_ALLOWED_ROLES);
}

export async function requireRegistryAccess(
  request: Parameters<typeof requireAuthenticatedRequest>[0],
  reply: Parameters<typeof requireAuthenticatedRequest>[1],
  persistence: CorePersistence,
) {
  return requireAuthenticatedRequest(request, reply, persistence, REGISTRY_ALLOWED_ROLES);
}

export async function requireRegistryWriteAccess(
  request: Parameters<typeof requireAuthenticatedRequest>[0],
  reply: Parameters<typeof requireAuthenticatedRequest>[1],
  persistence: CorePersistence,
) {
  return requireAuthenticatedRequest(request, reply, persistence, REGISTRY_WRITE_ALLOWED_ROLES);
}

export async function requireQualityAccess(
  request: Parameters<typeof requireAuthenticatedRequest>[0],
  reply: Parameters<typeof requireAuthenticatedRequest>[1],
  persistence: CorePersistence,
) {
  return requireAuthenticatedRequest(request, reply, persistence, QUALITY_ALLOWED_ROLES);
}

export async function requireQualityWriteAccess(
  request: Parameters<typeof requireAuthenticatedRequest>[0],
  reply: Parameters<typeof requireAuthenticatedRequest>[1],
  persistence: CorePersistence,
) {
  return requireAuthenticatedRequest(request, reply, persistence, QUALITY_WRITE_ALLOWED_ROLES);
}

export async function requireSettingsAccess(
  request: Parameters<typeof requireAuthenticatedRequest>[0],
  reply: Parameters<typeof requireAuthenticatedRequest>[1],
  persistence: CorePersistence,
) {
  return requireAuthenticatedRequest(request, reply, persistence, SETTINGS_ALLOWED_ROLES);
}

export async function requireSettingsWriteAccess(
  request: Parameters<typeof requireAuthenticatedRequest>[0],
  reply: Parameters<typeof requireAuthenticatedRequest>[1],
  persistence: CorePersistence,
) {
  return requireAuthenticatedRequest(request, reply, persistence, SETTINGS_WRITE_ALLOWED_ROLES);
}

function readRedirectTarget(body: unknown) {
  if (!body || typeof body !== "object") {
    return null;
  }

  const value = "redirectTo" in body ? body.redirectTo : null;
  return typeof value === "string" && value.length > 0 ? value : null;
}

function isConflictError(error: unknown) {
  return error instanceof Error && /unique|constraint|already exists|duplicate/i.test(error.message);
}
