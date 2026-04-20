import { initTRPC } from "@trpc/server";

export interface AppContext {
  requestId: string;
}

const t = initTRPC.context<AppContext>().create();

export const router = t.router;
export const publicProcedure = t.procedure;
export const middleware = t.middleware;
export const createCallerFactory = t.createCallerFactory;
