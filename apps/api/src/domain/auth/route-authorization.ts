import type { FastifyInstance, FastifyReply, FastifyRequest } from "fastify";

import {
  findRouteEntry,
  loadRouteAuthorizationMatrix,
} from "../../config/route-authorization-matrix.js";
import type { CorePersistence } from "./core-persistence.js";
import { hasAnyRole, resolveAuthenticatedRequest } from "./session-auth.js";

const MUTABLE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export function registerRouteAuthorizationHook(app: FastifyInstance, corePersistence: CorePersistence) {
  const matrix = loadRouteAuthorizationMatrix();

  app.addHook("onRequest", async (request: FastifyRequest, reply: FastifyReply) => {
    // Only enforce mutable routes at this layer.
    // GET/HEAD routes rely on per-handler authorization, which supports
    // conditional public access (e.g. canonical catalog with ?scenario).
    if (!MUTABLE_METHODS.has(request.method)) {
      return;
    }

    const routePath = request.routeOptions.url ?? "";
    const entry = findRouteEntry(matrix, routePath, request.method);

    if (!entry) {
      reply.code(503).send({ error: "route_not_in_authorization_matrix" });
      return;
    }

    if (entry.public) {
      return;
    }

    const context = await resolveAuthenticatedRequest(request, corePersistence);
    if (!context) {
      reply.code(401).send({ error: "authentication_required" });
      return;
    }

    if (entry.roles.length > 0) {
      const allowed = hasAnyRole(
        context.user.roles,
        entry.roles as import("@afere/contracts").MembershipRole[],
      );
      if (!allowed) {
        reply.code(403).send({ error: "forbidden" });
        return;
      }
    }

    // Decorate request so downstream handlers can reuse the context
    // without resolving the session again.
    request.authContext = context;
  });
}
