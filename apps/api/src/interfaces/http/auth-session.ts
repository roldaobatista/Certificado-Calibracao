import { randomBytes } from "node:crypto";

import {
  authLoginResponseSchema,
  authSessionSchema,
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
export const SERVICE_ORDER_WRITE_ALLOWED_ROLES: MembershipRole[] = [
  "admin",
  "quality_manager",
  "signatory",
  "technical_reviewer",
  "technician",
];

export async function registerAuthSessionRoutes(
  app: FastifyInstance,
  persistence: CorePersistence,
) {
  app.get("/auth/session", async (request, reply) => {
    const session = await resolveAuthenticatedRequest(request, persistence);
    const payload: AuthSession = session ? toAuthSession(session) : { authenticated: false };
    return reply.code(200).send(authSessionSchema.parse(payload));
  });

  app.post("/auth/login", async (request, reply) => {
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

    const token = createSessionToken();
    const expiresAt = createSessionExpiry();
    const session = await persistence.createSession({
      organizationId: user.organizationId,
      userId: user.userId,
      tokenHash: hashSessionToken(token),
      expiresAt,
    });

    await persistence.touchUserLogin(user.userId, new Date());
    issueSessionCookie(reply, token, expiresAt);

    const payload: AuthLoginResponse = {
      ok: true,
      session: toAuthSession(session),
    };

    if (body.data.redirectTo) {
      return reply.redirect(body.data.redirectTo);
    }

    return reply.code(200).send(authLoginResponseSchema.parse(payload));
  });

  app.post("/auth/logout", async (request, reply) => {
    const session = await resolveAuthenticatedRequest(request, persistence);
    if (session) {
      await persistence.revokeSessionByTokenHash(session.tokenHash);
    }

    clearSessionCookie(reply);
    const redirectTo = readRedirectTarget(request.body);

    if (redirectTo) {
      return reply.redirect(redirectTo);
    }

    return reply.code(204).send();
  });

  app.post("/onboarding/bootstrap", async (request, reply) => {
    const body = BootstrapBodySchema.safeParse(request.body);
    if (!body.success) {
      return reply.code(400).send({ error: "invalid_body" });
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

    return reply.redirect(body.data.redirectTo ?? "http://127.0.0.1:3002/auth/login?created=1");
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
