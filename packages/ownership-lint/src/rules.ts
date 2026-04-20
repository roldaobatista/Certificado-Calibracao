import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { load as yamlLoad } from "js-yaml";
import { z } from "zod";

export const Severity = z.enum(["error", "warning", "info"]);
export type Severity = z.infer<typeof Severity>;

const OwnershipRuleSchema = z.object({
  id: z.string().regex(/^OWN-\d{3}$/),
  scope: z.array(z.string()).min(1),
  forbidden_imports: z.array(z.string()).min(1),
  severity: Severity,
  reason: z.string().min(1),
  suggestion: z.string().min(1),
});
export type OwnershipRule = z.infer<typeof OwnershipRuleSchema>;

const CoverageSchema = z.object({ exclude: z.array(z.string()).default([]) });
export type Coverage = z.infer<typeof CoverageSchema>;

const RulesFileSchema = z.object({
  rules: z.array(OwnershipRuleSchema).min(1),
  coverage: CoverageSchema,
});
export type RulesFile = z.infer<typeof RulesFileSchema>;

export function loadRules(path?: string): RulesFile {
  const filePath = path ?? resolve(dirname(fileURLToPath(import.meta.url)), "rules.yaml");
  const raw = readFileSync(filePath, "utf8");
  const parsed = yamlLoad(raw);
  return RulesFileSchema.parse(parsed);
}
