import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

import type { EmissionDryRunProfile, EmissionDryRunResult } from "@afere/contracts";

export interface EmissionDryRunScenarioLike {
  id: string;
  label: string;
  result: EmissionDryRunResult;
}

export interface EmitCertDryCliOptions {
  profile?: EmissionDryRunProfile;
  scenario?: string;
  json?: boolean;
}

export function parseEmitCertDryArgs(args: string[]): EmitCertDryCliOptions {
  const options: EmitCertDryCliOptions = {};

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (!arg) continue;

    if (arg === "--json") {
      options.json = true;
      continue;
    }

    if (arg === "--profile") {
      const value = args[index + 1];
      if (value === "A" || value === "B" || value === "C") {
        options.profile = value;
        index += 1;
        continue;
      }
      throw new Error("invalid_profile");
    }

    if (arg === "--scenario") {
      const value = args[index + 1];
      if (!value) {
        throw new Error("missing_scenario");
      }
      options.scenario = value;
      index += 1;
      continue;
    }

    throw new Error(`unknown_argument:${arg}`);
  }

  return options;
}

export async function resolveEmitCertDryScenario(
  options: EmitCertDryCliOptions,
): Promise<EmissionDryRunScenarioLike> {
  const module = await import("../apps/api/src/domain/emission/dry-run-scenarios.js");

  if (options.scenario) {
    return module.resolveEmissionDryRunScenario(options.scenario);
  }

  if (options.profile) {
    return module.resolveEmissionDryRunScenarioByProfile(options.profile);
  }

  return module.resolveEmissionDryRunScenarioByProfile("B");
}

export function renderEmissionDryRunReport(
  scenario: EmissionDryRunScenarioLike,
  result: EmissionDryRunResult = scenario.result,
): string {
  const lines = [
    `Scenario: ${scenario.id} (${scenario.label})`,
    `Profile: ${result.profile}`,
    `Status: ${result.status.toUpperCase()}`,
    `Summary: ${result.summary}`,
    `Template: ${result.artifacts.templateId}`,
    `Symbol policy: ${result.artifacts.symbolPolicy}`,
  ];

  if (result.artifacts.certificateNumber) {
    lines.push(`Certificate: ${result.artifacts.certificateNumber}`);
  }
  if (result.artifacts.qrCodeUrl) {
    lines.push(`QR: ${result.artifacts.qrCodeUrl}`);
  }
  if (result.artifacts.declarationSummary) {
    lines.push(`Declaration: ${result.artifacts.declarationSummary}`);
  }
  if (result.warnings.length > 0) {
    lines.push(`Warnings: ${result.warnings.join(" | ")}`);
  }
  if (result.blockers.length > 0) {
    lines.push(`Blockers: ${result.blockers.join(" | ")}`);
  }

  lines.push("Checks:");
  for (const check of result.checks) {
    lines.push(`- [${check.status === "passed" ? "OK" : "FAIL"}] ${check.title}: ${check.detail}`);
  }

  return lines.join("\n");
}

export async function runEmitCertDryCli(args: string[]): Promise<{
  exitCode: number;
  output: string;
}> {
  try {
    const options = parseEmitCertDryArgs(args);
    const scenario = await resolveEmitCertDryScenario(options);

    if (options.json) {
      return {
        exitCode: scenario.result.status === "ready" ? 0 : 1,
        output: JSON.stringify(
          {
            scenario: scenario.id,
            label: scenario.label,
            result: scenario.result,
          },
          null,
          2,
        ),
      };
    }

    return {
      exitCode: scenario.result.status === "ready" ? 0 : 1,
      output: renderEmissionDryRunReport(scenario),
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : "unknown_error";
    return {
      exitCode: 1,
      output: `emit-cert-dry error: ${message}`,
    };
  }
}

export function isEmitCertDryCliEntry(metaUrl: string = import.meta.url): boolean {
  const entryPath = process.argv[1];
  if (!entryPath) {
    return false;
  }

  return pathToFileURL(resolve(entryPath)).href === metaUrl;
}

if (isEmitCertDryCliEntry()) {
  void runEmitCertDryCli(process.argv.slice(2)).then((result) => {
    if (result.output.length > 0) {
      const writer = result.exitCode === 0 ? process.stdout : process.stderr;
      writer.write(`${result.output}\n`);
    }
    process.exit(result.exitCode);
  });
}
