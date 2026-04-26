import { createHash, randomBytes } from "node:crypto";

import type { AuthSession, AuthSessionUser, MembershipRole } from "@afere/contracts";
import type { FastifyReply, FastifyRequest } from "fastify";

import type { CorePersistence, PersistedSessionRecord, PersistedUserRecord } from "./core-persistence.js";

export const SESSION_COOKIE_NAME = "afere_session";
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

export type AuthenticatedRequestContext = {
  sessionId: string;
  tokenHash: string;
  expiresAtUtc: string;
  user: PersistedUserRecord;
};

export async function resolveAuthenticatedRequest(
  request: FastifyRequest,
  persistence: CorePersistence,
): Promise<AuthenticatedRequestContext | null> {
  const token = readSessionToken(request.headers.cookie);
  if (!token) {
    return null;
  }

  const tokenHash = hashSessionToken(token);
  const session = await persistence.findSessionByTokenHash(tokenHash);
  if (!session || new Date(session.expiresAtUtc).getTime() <= Date.now()) {
    return null;
  }

  return {
    sessionId: session.sessionId,
    tokenHash,
    expiresAtUtc: session.expiresAtUtc,
    user: session.user,
  };
}

export async function requireAuthenticatedRequest(
  request: FastifyRequest,
  reply: FastifyReply,
  persistence: CorePersistence,
  allowedRoles?: MembershipRole[],
): Promise<AuthenticatedRequestContext | null> {
  const context = await resolveAuthenticatedRequest(request, persistence);

  if (!context) {
    await reply.code(401).send({ error: "authentication_required" });
    return null;
  }

  if (allowedRoles && allowedRoles.length > 0 && !hasAnyRole(context.user.roles, allowedRoles)) {
    await reply.code(403).send({ error: "forbidden" });
    return null;
  }

  return context;
}

export function issueSessionCookie(
  reply: FastifyReply,
  sessionToken: string,
  expiresAt: Date,
  opts?: { secure?: boolean; sameSite?: "Strict" | "Lax" | "None" },
) {
  reply.header("set-cookie", serializeSessionCookie(sessionToken, expiresAt, opts));
}

export function clearSessionCookie(reply: FastifyReply, opts?: { secure?: boolean; sameSite?: "Strict" | "Lax" | "None" }) {
  reply.header("set-cookie", clearSessionCookieValue(opts));
}

export function createSessionToken() {
  return randomBytes(32).toString("base64url");
}

export function hashSessionToken(token: string) {
  return createHash("sha256").update(token).digest("base64url");
}

export function createSessionExpiry(now = new Date()) {
  return new Date(now.getTime() + ONE_DAY_MS);
}

export function toAuthSession(session: { user: PersistedUserRecord; expiresAtUtc: string }): AuthSession {
  const user = session.user;

  return {
    authenticated: true,
    user: toAuthSessionUser(user),
    expiresAtUtc: session.expiresAtUtc,
  };
}

export function toAuthSessionUser(user: PersistedUserRecord): AuthSessionUser {
  return {
    userId: user.userId,
    organizationId: user.organizationId,
    organizationName: user.organizationName,
    organizationSlug: user.organizationSlug,
    email: user.email,
    displayName: user.displayName,
    roles: user.roles,
    mfaEnrolled: user.mfaEnrolled,
  };
}

export function hasPrivilegedRole(roles: MembershipRole[]) {
  return hasAnyRole(roles, ["admin", "signatory"]);
}

export function hasAnyRole(userRoles: MembershipRole[], allowedRoles: MembershipRole[]) {
  return allowedRoles.some((role) => userRoles.includes(role));
}

function readSessionToken(cookieHeader: string | string[] | undefined): string | null {
  if (!cookieHeader) {
    return null;
  }

  const source = Array.isArray(cookieHeader) ? cookieHeader.join("; ") : cookieHeader;
  const segments = source.split(";").map((segment) => segment.trim());

  for (const segment of segments) {
    if (!segment.startsWith(`${SESSION_COOKIE_NAME}=`)) {
      continue;
    }

    const value = segment.slice(`${SESSION_COOKIE_NAME}=`.length);
    return value.length > 0 ? decodeURIComponent(value) : null;
  }

  return null;
}

function serializeSessionCookie(token: string, expiresAt: Date, opts?: { secure?: boolean; sameSite?: "Strict" | "Lax" | "None" }) {
  const maxAgeSec = Math.max(0, Math.floor((expiresAt.getTime() - Date.now()) / 1000));
  const flags = [
    `${SESSION_COOKIE_NAME}=${encodeURIComponent(token)}`,
    "Path=/",
    "HttpOnly",
    `SameSite=${opts?.sameSite ?? "Lax"}`,
    `Expires=${expiresAt.toUTCString()}`,
    `Max-Age=${maxAgeSec}`,
  ];
  if (opts?.secure) {
    flags.push("Secure");
  }
  return flags.join("; ");
}

function clearSessionCookieValue(opts?: { secure?: boolean; sameSite?: "Strict" | "Lax" | "None" }) {
  const flags = [
    `${SESSION_COOKIE_NAME}=`,
    "Path=/",
    "HttpOnly",
    `SameSite=${opts?.sameSite ?? "Lax"}`,
    "Expires=Thu, 01 Jan 1970 00:00:00 GMT",
    "Max-Age=0",
  ];
  if (opts?.secure) {
    flags.push("Secure");
  }
  return flags.join("; ");
}
