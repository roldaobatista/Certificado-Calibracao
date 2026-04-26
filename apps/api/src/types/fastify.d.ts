import type { AuthenticatedRequestContext } from "../domain/auth/session-auth.js";

declare module "fastify" {
  interface FastifyRequest {
    authContext?: AuthenticatedRequestContext;
  }
}
