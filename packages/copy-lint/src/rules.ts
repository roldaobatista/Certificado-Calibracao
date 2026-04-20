import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { load as yamlLoad } from "js-yaml";
import { z } from "zod";

export const Severity = z.enum(["error", "warning", "info"]);
export type Severity = z.infer<typeof Severity>;

const RuleSchema = z.object({
  id: z.string().regex(/^CL-\d{3}$/),
  pattern: z.string().min(1),
  severity: Severity,
  reason: z.string().min(1),
  suggestion: z.string().min(1),
});
export type Rule = z.infer<typeof RuleSchema>;

const CoverageSchema = z.object({
  include: z.array(z.string()).default([]),
  exclude: z.array(z.string()).default([]),
});
export type Coverage = z.infer<typeof CoverageSchema>;

const RulesFileSchema = z.object({
  forbidden: z.array(RuleSchema).min(1),
  coverage: CoverageSchema,
});
export type RulesFile = z.infer<typeof RulesFileSchema>;

export interface CompiledRule extends Rule {
  regex: RegExp;
}

export function compileRules(rules: Rule[]): CompiledRule[] {
  return rules.map((rule) => ({
    ...rule,
    regex: new RegExp(rule.pattern, "giu"),
  }));
}

export function loadRules(path?: string): RulesFile & { compiled: CompiledRule[] } {
  const filePath = path ?? resolve(dirname(fileURLToPath(import.meta.url)), "rules.yaml");
  const raw = readFileSync(filePath, "utf8");
  const parsed = yamlLoad(raw);
  const validated = RulesFileSchema.parse(parsed);
  return { ...validated, compiled: compileRules(validated.forbidden) };
}
