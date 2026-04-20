import { fastifyTRPCPlugin, type FastifyTRPCPluginOptions } from "@trpc/server/adapters/fastify";
import fp from "fastify-plugin";
import { appRouter, type AppRouter, type AppContext } from "@afere/contracts";

export const trpcPlugin = fp(async (app) => {
  const options: FastifyTRPCPluginOptions<AppRouter> = {
    prefix: "/trpc",
    trpcOptions: {
      router: appRouter,
      createContext: ({ req }): AppContext => {
        const requestId = (req.headers["x-request-id"] as string | undefined) ?? req.id ?? crypto.randomUUID();
        return { requestId };
      },
      onError: ({ error, path }) => {
        app.log.error({ err: error, path }, "trpc procedure error");
      },
    },
  };
  await app.register(fastifyTRPCPlugin, options);
});
