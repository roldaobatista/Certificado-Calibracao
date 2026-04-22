import { z } from "zod";

export const registryOperationalStatusSchema = z.enum(["ready", "attention", "blocked"]);
export type RegistryOperationalStatus = z.infer<typeof registryOperationalStatusSchema>;

export const registryScenarioIdSchema = z.enum([
  "operational-ready",
  "certificate-attention",
  "registration-blocked",
]);
export type RegistryScenarioId = z.infer<typeof registryScenarioIdSchema>;
