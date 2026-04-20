#!/usr/bin/env node
import { appendFileSync, existsSync, mkdirSync, readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

type CliName = "claude" | "codex" | "unknown";
type HookName = "PreToolUse" | "PostToolUse" | "manual";
type BudgetEventType = "consumption" | "alert" | "block";

export interface BudgetEvent {
  version: 1;
  ts: string;
  date: string;
  type: BudgetEventType;
  cli: CliName;
  hook: HookName;
  toolName: string;
  taskId?: string;
  prId?: string;
  inputTokens?: number;
  outputTokens?: number;
  totalTokens: number;
  costUsd: number;
  metadataMissing: boolean;
  code?: string;
  message?: string;
}

export interface RecordBudgetEventOptions {
  root?: string;
  now?: Date;
  cli?: CliName;
  hook?: HookName;
  toolName?: string;
  taskId?: string;
  prId?: string;
  inputTokens?: number;
  outputTokens?: number;
  totalTokens?: number;
  costUsd?: number;
}

export interface CheckBudgetOptions {
  root?: string;
  now?: Date;
  cli?: CliName;
  hook?: HookName;
  toolName?: string;
  taskId?: string;
  prId?: string;
  currentInputTokens?: number;
  currentOutputTokens?: number;
  currentTotalTokens?: number;
  currentCostUsd?: number;
  writeEvents?: boolean;
}

export interface BudgetCheckResult {
  blocked: boolean;
  messages: string[];
}

interface BudgetCaps {
  tokens: {
    perToolCallSoft: number;
    perToolCallHard: number;
    perTaskSoft: number;
    perTaskHard: number;
    perPrSoft: number;
    perPrHard: number;
    contextRotSoft: number;
    contextRotHard: number;
  };
  costUSD: {
    perDevPerDaySoft: number;
    perDevPerDayHard: number;
    perDevPerWeekSoft: number;
    perDevPerWeekHard: number;
    perPrSoft: number;
    perPrHard: number;
    perCloudTaskSoft: number;
    perCloudTaskHard: number;
  };
}

interface Threshold {
  code: string;
  value: number;
  soft: number;
  hard: number;
  unit: "tokens" | "USD";
}

const DEFAULT_CLI: CliName = "unknown";
const DEFAULT_HOOK: HookName = "manual";
const DEFAULT_TOOL = "unknown";

export function recordBudgetEvent(options: RecordBudgetEventOptions): { path: string; event: BudgetEvent } {
  const root = resolve(options.root ?? process.cwd());
  const now = options.now ?? new Date();
  const event = makeConsumptionEvent(options, now);
  const path = appendBudgetEvent(root, event);
  return { path, event };
}

export function checkBudget(options: CheckBudgetOptions): BudgetCheckResult {
  const root = resolve(options.root ?? process.cwd());
  const now = options.now ?? new Date();
  const caps = loadBudgetCaps(root);
  const events = readBudgetEvents(root);
  const consumptionEvents = events.filter((event) => event.type === "consumption");
  const currentTotalTokens = normalizeTokenTotal(
    options.currentInputTokens,
    options.currentOutputTokens,
    options.currentTotalTokens,
  );
  const currentCostUsd = normalizeNumber(options.currentCostUsd);
  const today = dateKey(now);
  const weekStart = startOfUtcWeek(now);

  const thresholds: Threshold[] = [
    {
      code: "BUDGET-TOKENS-TOOL",
      value: currentTotalTokens,
      soft: caps.tokens.perToolCallSoft,
      hard: caps.tokens.perToolCallHard,
      unit: "tokens",
    },
    {
      code: "BUDGET-USD-DAY",
      value: sum(consumptionEvents.filter((event) => event.date === today), "costUsd") + currentCostUsd,
      soft: caps.costUSD.perDevPerDaySoft,
      hard: caps.costUSD.perDevPerDayHard,
      unit: "USD",
    },
    {
      code: "BUDGET-USD-WEEK",
      value: sum(consumptionEvents.filter((event) => event.ts >= weekStart.toISOString()), "costUsd") + currentCostUsd,
      soft: caps.costUSD.perDevPerWeekSoft,
      hard: caps.costUSD.perDevPerWeekHard,
      unit: "USD",
    },
  ];

  if (options.taskId) {
    thresholds.push({
      code: "BUDGET-TOKENS-TASK",
      value: sum(consumptionEvents.filter((event) => event.taskId === options.taskId), "totalTokens") + currentTotalTokens,
      soft: caps.tokens.perTaskSoft,
      hard: caps.tokens.perTaskHard,
      unit: "tokens",
    });
  }

  if (options.prId) {
    const prEvents = consumptionEvents.filter((event) => event.prId === options.prId);
    thresholds.push(
      {
        code: "BUDGET-TOKENS-PR",
        value: sum(prEvents, "totalTokens") + currentTotalTokens,
        soft: caps.tokens.perPrSoft,
        hard: caps.tokens.perPrHard,
        unit: "tokens",
      },
      {
        code: "BUDGET-USD-PR",
        value: sum(prEvents, "costUsd") + currentCostUsd,
        soft: caps.costUSD.perPrSoft,
        hard: caps.costUSD.perPrHard,
        unit: "USD",
      },
    );
  }

  const messages: string[] = [];
  let blocked = false;
  for (const threshold of thresholds) {
    if (threshold.value > threshold.hard) {
      blocked = true;
      messages.push(formatMessage(`${threshold.code}-HARD`, threshold.value, threshold.hard, threshold.unit));
      continue;
    }
    if (threshold.value > threshold.soft) {
      messages.push(formatMessage(`${threshold.code}-SOFT`, threshold.value, threshold.soft, threshold.unit));
    }
  }

  if (options.writeEvents) {
    for (const message of messages) {
      appendBudgetEvent(root, {
        version: 1,
        ts: now.toISOString(),
        date: today,
        type: message.includes("-HARD ") ? "block" : "alert",
        cli: options.cli ?? DEFAULT_CLI,
        hook: options.hook ?? DEFAULT_HOOK,
        toolName: options.toolName ?? DEFAULT_TOOL,
        taskId: options.taskId,
        prId: options.prId,
        totalTokens: currentTotalTokens,
        costUsd: currentCostUsd,
        metadataMissing: currentTotalTokens === 0 && currentCostUsd === 0,
        code: message.split(" ")[0],
        message,
      });
    }
  }

  return { blocked, messages };
}

function makeConsumptionEvent(options: RecordBudgetEventOptions, now: Date): BudgetEvent {
  const totalTokens = normalizeTokenTotal(options.inputTokens, options.outputTokens, options.totalTokens);
  const costUsd = normalizeNumber(options.costUsd);
  return {
    version: 1,
    ts: now.toISOString(),
    date: dateKey(now),
    type: "consumption",
    cli: options.cli ?? DEFAULT_CLI,
    hook: options.hook ?? DEFAULT_HOOK,
    toolName: options.toolName ?? DEFAULT_TOOL,
    taskId: options.taskId,
    prId: options.prId,
    inputTokens: options.inputTokens,
    outputTokens: options.outputTokens,
    totalTokens,
    costUsd,
    metadataMissing:
      options.inputTokens === undefined &&
      options.outputTokens === undefined &&
      options.totalTokens === undefined &&
      options.costUsd === undefined,
  };
}

function loadBudgetCaps(root: string): BudgetCaps {
  const path = join(root, ".claude", "settings.json");
  if (!existsSync(path)) throw new Error(`BUDGET-CONFIG-001 ${path} ausente`);
  const parsed = JSON.parse(readFileSync(path, "utf8")) as { budgets?: BudgetCaps };
  if (!parsed.budgets) throw new Error("BUDGET-CONFIG-002 .claude/settings.json sem budgets");
  return parsed.budgets;
}

function readBudgetEvents(root: string): BudgetEvent[] {
  const dir = join(root, "compliance", "budget-log");
  if (!existsSync(dir)) return [];
  const events: BudgetEvent[] = [];
  for (const file of readdirSync(dir).filter((name) => /^\d{4}-\d{2}-\d{2}\.jsonl$/.test(name)).sort()) {
    const path = join(dir, file);
    const lines = readFileSync(path, "utf8").split(/\r?\n/).filter(Boolean);
    for (const [index, line] of lines.entries()) {
      try {
        events.push(JSON.parse(line) as BudgetEvent);
      } catch {
        throw new Error(`BUDGET-LOG-001 ${path}:${index + 1} JSON invalido`);
      }
    }
  }
  return events;
}

function appendBudgetEvent(root: string, event: BudgetEvent): string {
  const dir = join(root, "compliance", "budget-log");
  mkdirSync(dir, { recursive: true });
  const path = join(dir, `${event.date}.jsonl`);
  appendFileSync(path, `${JSON.stringify(stripUndefined(event))}\n`, "utf8");
  return path;
}

function normalizeTokenTotal(inputTokens?: number, outputTokens?: number, totalTokens?: number): number {
  if (totalTokens !== undefined) return normalizeNumber(totalTokens);
  return normalizeNumber(inputTokens) + normalizeNumber(outputTokens);
}

function normalizeNumber(value?: number): number {
  if (value === undefined || Number.isNaN(value)) return 0;
  if (!Number.isFinite(value) || value < 0) throw new Error(`BUDGET-ARG-001 numero invalido: ${value}`);
  return value;
}

function dateKey(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function startOfUtcWeek(date: Date): Date {
  const start = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  const day = start.getUTCDay();
  const diff = day === 0 ? 6 : day - 1;
  start.setUTCDate(start.getUTCDate() - diff);
  return start;
}

function sum(events: BudgetEvent[], field: "totalTokens" | "costUsd"): number {
  return events.reduce((total, event) => total + normalizeNumber(event[field]), 0);
}

function formatMessage(code: string, value: number, limit: number, unit: Threshold["unit"]): string {
  const formattedValue = unit === "USD" ? value.toFixed(4) : String(value);
  const formattedLimit = unit === "USD" ? limit.toFixed(4) : String(limit);
  return `${code} ${formattedValue}/${formattedLimit} ${unit}`;
}

function stripUndefined<T extends Record<string, unknown>>(value: T): T {
  return Object.fromEntries(Object.entries(value).filter(([, entry]) => entry !== undefined)) as T;
}

interface ParsedCli {
  command: "check" | "record";
  options: RecordBudgetEventOptions & CheckBudgetOptions;
}

function parseArgs(argv: string[]): ParsedCli {
  const command = argv.shift();
  if (command !== "check" && command !== "record") {
    throw new Error("uso: budget-tracker <check|record> [opcoes]");
  }
  const options: RecordBudgetEventOptions & CheckBudgetOptions = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];
    const requireValue = (): string => {
      if (!next) throw new Error(`${arg} exige valor`);
      i += 1;
      return next;
    };
    if (arg === "--workspace") options.root = requireValue();
    else if (arg === "--cli") options.cli = parseCliName(requireValue());
    else if (arg === "--hook") options.hook = parseHookName(requireValue());
    else if (arg === "--tool") options.toolName = requireValue();
    else if (arg === "--task-id") options.taskId = requireValue();
    else if (arg === "--pr-id") options.prId = requireValue();
    else if (arg === "--input-tokens") {
      const value = parseNumericArg(arg, requireValue());
      options.inputTokens = value;
      options.currentInputTokens = value;
    } else if (arg === "--output-tokens") {
      const value = parseNumericArg(arg, requireValue());
      options.outputTokens = value;
      options.currentOutputTokens = value;
    } else if (arg === "--tokens") {
      const value = parseNumericArg(arg, requireValue());
      options.totalTokens = value;
      options.currentTotalTokens = value;
    } else if (arg === "--cost-usd") {
      const value = parseNumericArg(arg, requireValue());
      options.costUsd = value;
      options.currentCostUsd = value;
    } else if (arg === "--write-events") {
      options.writeEvents = true;
    } else {
      throw new Error(`argumento desconhecido: ${arg}`);
    }
  }
  return { command, options };
}

function parseNumericArg(name: string, value: string): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) throw new Error(`${name} invalido: ${value}`);
  return parsed;
}

function parseCliName(value: string): CliName {
  if (value === "claude" || value === "codex" || value === "unknown") return value;
  return "unknown";
}

function parseHookName(value: string): HookName {
  if (value === "PreToolUse" || value === "PostToolUse" || value === "manual") return value;
  return "manual";
}

function main(): void {
  try {
    const parsed = parseArgs(process.argv.slice(2));
    if (parsed.command === "record") {
      const { event, path } = recordBudgetEvent(parsed.options);
      console.log(`budget-tracker: recorded ${event.totalTokens} tokens, $${event.costUsd.toFixed(4)} in ${path}`);
      return;
    }

    const result = checkBudget(parsed.options);
    for (const message of result.messages) console.log(message);
    if (result.blocked) {
      console.error("budget-tracker: hard cap excedido; bloqueando tool call");
      process.exit(1);
    }
    console.log(result.messages.length > 0 ? "budget-tracker: soft cap alertado" : "budget-tracker: ok");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`budget-tracker: ${message}`);
    process.exit(2);
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  main();
}
