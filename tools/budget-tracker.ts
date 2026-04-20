#!/usr/bin/env node
import { appendFileSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

type CliName = "claude" | "codex" | "unknown";
type HookName = "PreToolUse" | "PostToolUse" | "manual";
type BudgetEventType = "consumption" | "alert" | "block" | "control";
type BudgetControlKind =
  | "concurrency"
  | "tool_error"
  | "file_edit"
  | "regulatory_failure"
  | "tenancy_failure"
  | "hash_chain_divergence"
  | "worktree_heartbeat";
type BudgetTier = "tier1" | "tier2" | "tier3";
type BudgetControlStatus = "start" | "finish" | "failure" | "success";

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
  controlKind?: BudgetControlKind;
  tier?: BudgetTier;
  resourceId?: string;
  status?: BudgetControlStatus;
  filePath?: string;
  branch?: string;
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

export interface BudgetControlOptions {
  root?: string;
  now?: Date;
  cli?: CliName;
  hook?: HookName;
  toolName?: string;
  taskId?: string;
  prId?: string;
  controlKind: BudgetControlKind;
  tier?: BudgetTier;
  resourceId: string;
  status: BudgetControlStatus;
  filePath?: string;
  branch?: string;
}

export interface WeeklyBudgetReportOptions {
  root?: string;
  now?: Date;
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
  concurrency?: {
    tier1Subagents: number;
    tier2Worktrees: number;
    tier3CloudAgents: number;
  };
  circuitBreakers?: {
    consecutiveToolErrors: number;
    sameFileEdits: number;
    sameFileEditWindowMinutes: number;
    regulatoryFailures: number;
    tenancyFailures: number;
    hashChainDivergences: number;
    worktreeHeartbeatHours: number;
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

export function recordBudgetControlEvent(options: BudgetControlOptions): { path: string; event: BudgetEvent } {
  const root = resolve(options.root ?? process.cwd());
  const now = options.now ?? new Date();
  const event = makeControlEvent(options, now);
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

export function checkBudgetControls(options: BudgetControlOptions): BudgetCheckResult {
  const root = resolve(options.root ?? process.cwd());
  const now = options.now ?? new Date();
  const caps = loadBudgetCaps(root);
  const events = readBudgetEvents(root);
  const messages: string[] = [];

  if (options.controlKind === "concurrency" && options.status === "start") {
    if (!options.tier) throw new Error("BUDGET-ARG-002 tier obrigatorio para controle de concorrencia");
    const limit = concurrencyLimit(caps, options.tier);
    const active = activeConcurrency(events, options.tier);
    active.add(options.resourceId);
    if (active.size > limit) {
      messages.push(`BUDGET-CONCURRENCY-${options.tier.toUpperCase()}-HARD ${active.size}/${limit} active`);
    }
  }

  if (options.controlKind === "tool_error" && options.status === "failure") {
    if (!options.taskId) throw new Error("BUDGET-ARG-003 taskId obrigatorio para contador de tool errors");
    const limit = circuitBreakerCaps(caps).consecutiveToolErrors;
    const count = consecutiveToolErrors(events, options.taskId) + 1;
    if (count >= limit) {
      messages.push(`BUDGET-CIRCUIT-TOOL-ERRORS-HARD ${count}/${limit} consecutive`);
    }
  }

  if (options.controlKind === "file_edit") {
    if (!options.filePath) throw new Error("BUDGET-ARG-004 filePath obrigatorio para contador de edits");
    const circuitCaps = circuitBreakerCaps(caps);
    const count = fileEditsInWindow(
      events,
      options.filePath,
      now,
      circuitCaps.sameFileEditWindowMinutes,
    ) + 1;
    if (count >= circuitCaps.sameFileEdits) {
      messages.push(`BUDGET-CIRCUIT-FILE-EDITS-HARD ${count}/${circuitCaps.sameFileEdits} edits`);
    }
  }

  if (options.controlKind === "regulatory_failure" && options.status === "failure") {
    if (!options.branch) throw new Error("BUDGET-ARG-005 branch obrigatoria para falhas regulatorias");
    const limit = circuitBreakerCaps(caps).regulatoryFailures;
    const count = controlFailures(events, "regulatory_failure", options.branch) + 1;
    if (count >= limit) {
      messages.push(`BUDGET-CIRCUIT-REGULATORY-HARD ${count}/${limit} failures`);
    }
  }

  if (options.controlKind === "tenancy_failure" && options.status === "failure") {
    const limit = circuitBreakerCaps(caps).tenancyFailures;
    const branch = options.branch ?? "unknown";
    const count = controlFailures(events, "tenancy_failure", branch) + 1;
    if (count >= limit) {
      messages.push(`BUDGET-CIRCUIT-TENANCY-HARD ${count}/${limit} failures`);
    }
  }

  if (options.controlKind === "hash_chain_divergence" && options.status === "failure") {
    const limit = circuitBreakerCaps(caps).hashChainDivergences;
    const count = controlFailureCount(events, "hash_chain_divergence") + 1;
    if (count >= limit) {
      messages.push(`BUDGET-CIRCUIT-HASH-CHAIN-HARD ${count}/${limit} divergences`);
    }
  }

  if (options.controlKind === "worktree_heartbeat") {
    const stale = staleWorktreeHeartbeats(events, now, circuitBreakerCaps(caps).worktreeHeartbeatHours);
    for (const heartbeat of stale) {
      messages.push(`BUDGET-CIRCUIT-WORKTREE-HEARTBEAT-SOFT ${heartbeat.resourceId} stale ${heartbeat.ageHours.toFixed(2)}h`);
    }
  }

  return { blocked: messages.some((message) => message.includes("-HARD ")), messages };
}

export function generateWeeklyBudgetReport(options: WeeklyBudgetReportOptions = {}): { path: string; content: string } {
  const root = resolve(options.root ?? process.cwd());
  const now = options.now ?? new Date();
  const week = isoWeekKey(now);
  const weekStart = startOfUtcWeek(now);
  const weekEnd = new Date(weekStart);
  weekEnd.setUTCDate(weekEnd.getUTCDate() + 7);
  const events = readBudgetEvents(root).filter((event) => {
    const timestamp = Date.parse(event.ts);
    return Number.isFinite(timestamp) && timestamp >= weekStart.getTime() && timestamp < weekEnd.getTime();
  });
  const consumptionEvents = events.filter((event) => event.type === "consumption");
  const controlEvents = events.filter((event) => event.type === "control");
  const totalTokens = sum(consumptionEvents, "totalTokens");
  const totalCostUsd = sum(consumptionEvents, "costUsd");
  const consumptionRows = summarizeConsumption(consumptionEvents);
  const controlRows = summarizeControls(controlEvents);

  const content = [
    `# Budget semanal ${week}`,
    "",
    `Semana UTC: ${weekStart.toISOString().slice(0, 10)} a ${new Date(weekEnd.getTime() - 1).toISOString().slice(0, 10)}`,
    "",
    `Total tokens: ${totalTokens}`,
    `Total cost USD: ${totalCostUsd.toFixed(4)}`,
    "",
    "## Consumo por ferramenta",
    "",
    "| CLI | Tool | Tokens | Cost USD |",
    "|-----|------|--------|----------|",
    ...(consumptionRows.length > 0
      ? consumptionRows.map((row) => `| ${row.cli} | ${row.toolName} | ${row.totalTokens} | ${row.costUsd.toFixed(4)} |`)
      : ["| none | none | 0 | 0.0000 |"]),
    "",
    "## Eventos de controle",
    "",
    "| Tipo | Eventos |",
    "|------|---------|",
    ...(controlRows.length > 0
      ? controlRows.map((row) => `| ${row.controlKind} | ${row.count} |`)
      : ["| none | 0 |"]),
    "",
  ].join("\n");

  const dir = join(root, "compliance", "budget-log", "weekly");
  mkdirSync(dir, { recursive: true });
  const path = join(dir, `${week}.md`);
  writeFileSync(path, content, "utf8");
  return { path, content };
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

function makeControlEvent(options: BudgetControlOptions, now: Date): BudgetEvent {
  return {
    version: 1,
    ts: now.toISOString(),
    date: dateKey(now),
    type: "control",
    cli: options.cli ?? DEFAULT_CLI,
    hook: options.hook ?? DEFAULT_HOOK,
    toolName: options.toolName ?? DEFAULT_TOOL,
    taskId: options.taskId,
    prId: options.prId,
    totalTokens: 0,
    costUsd: 0,
    metadataMissing: false,
    controlKind: options.controlKind,
    tier: options.tier,
    resourceId: options.resourceId,
    status: options.status,
    filePath: options.filePath,
    branch: options.branch,
  };
}

function activeConcurrency(events: BudgetEvent[], tier: BudgetTier): Set<string> {
  const active = new Set<string>();
  for (const event of events) {
    if (event.type !== "control" || event.controlKind !== "concurrency" || event.tier !== tier || !event.resourceId) {
      continue;
    }
    if (event.status === "start") active.add(event.resourceId);
    if (event.status === "finish") active.delete(event.resourceId);
  }
  return active;
}

function concurrencyLimit(caps: BudgetCaps, tier: BudgetTier): number {
  const concurrency = caps.concurrency ?? {
    tier1Subagents: 5,
    tier2Worktrees: 3,
    tier3CloudAgents: 2,
  };
  if (tier === "tier1") return concurrency.tier1Subagents;
  if (tier === "tier2") return concurrency.tier2Worktrees;
  return concurrency.tier3CloudAgents;
}

function circuitBreakerCaps(caps: BudgetCaps): Required<BudgetCaps>["circuitBreakers"] {
  return caps.circuitBreakers ?? {
    consecutiveToolErrors: 3,
    sameFileEdits: 5,
    sameFileEditWindowMinutes: 10,
    regulatoryFailures: 2,
    tenancyFailures: 1,
    hashChainDivergences: 1,
    worktreeHeartbeatHours: 4,
  };
}

function consecutiveToolErrors(events: BudgetEvent[], taskId: string): number {
  let count = 0;
  for (const event of [...events].reverse()) {
    if (event.type !== "control" || event.taskId !== taskId) continue;
    if (event.controlKind === "tool_error" && event.status === "failure") {
      count += 1;
      continue;
    }
    if (event.controlKind === "tool_error" && event.status === "success") break;
  }
  return count;
}

function fileEditsInWindow(events: BudgetEvent[], filePath: string, now: Date, windowMinutes: number): number {
  const windowStart = now.getTime() - windowMinutes * 60 * 1000;
  return events.filter((event) => {
    if (event.type !== "control" || event.controlKind !== "file_edit" || event.filePath !== filePath) return false;
    const timestamp = Date.parse(event.ts);
    return Number.isFinite(timestamp) && timestamp >= windowStart && timestamp <= now.getTime();
  }).length;
}

function controlFailures(events: BudgetEvent[], kind: BudgetControlKind, branch: string): number {
  return events.filter(
    (event) =>
      event.type === "control" &&
      event.controlKind === kind &&
      event.status === "failure" &&
      event.branch === branch,
  ).length;
}

function controlFailureCount(events: BudgetEvent[], kind: BudgetControlKind): number {
  return events.filter(
    (event) => event.type === "control" && event.controlKind === kind && event.status === "failure",
  ).length;
}

function staleWorktreeHeartbeats(
  events: BudgetEvent[],
  now: Date,
  maxAgeHours: number,
): Array<{ resourceId: string; ageHours: number }> {
  const latestByResource = new Map<string, Date>();
  for (const event of events) {
    if (event.type !== "control" || event.controlKind !== "worktree_heartbeat" || !event.resourceId) continue;
    const timestamp = new Date(event.ts);
    const current = latestByResource.get(event.resourceId);
    if (!current || timestamp > current) latestByResource.set(event.resourceId, timestamp);
  }

  const nowMs = now.getTime();
  return [...latestByResource.entries()]
    .map(([resourceId, timestamp]) => ({
      resourceId,
      ageHours: (nowMs - timestamp.getTime()) / (60 * 60 * 1000),
    }))
    .filter((heartbeat) => heartbeat.ageHours > maxAgeHours);
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

function isoWeekKey(date: Date): string {
  const utc = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  const day = utc.getUTCDay() || 7;
  utc.setUTCDate(utc.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(utc.getUTCFullYear(), 0, 1));
  const week = Math.ceil(((utc.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
  return `${utc.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}

function sum(events: BudgetEvent[], field: "totalTokens" | "costUsd"): number {
  return events.reduce((total, event) => total + normalizeNumber(event[field]), 0);
}

function formatMessage(code: string, value: number, limit: number, unit: Threshold["unit"]): string {
  const formattedValue = unit === "USD" ? value.toFixed(4) : String(value);
  const formattedLimit = unit === "USD" ? limit.toFixed(4) : String(limit);
  return `${code} ${formattedValue}/${formattedLimit} ${unit}`;
}

function summarizeConsumption(events: BudgetEvent[]): Array<{
  cli: CliName;
  toolName: string;
  totalTokens: number;
  costUsd: number;
}> {
  const rows = new Map<string, { cli: CliName; toolName: string; totalTokens: number; costUsd: number }>();
  for (const event of events) {
    const key = `${event.cli}\0${event.toolName}`;
    const row = rows.get(key) ?? { cli: event.cli, toolName: event.toolName, totalTokens: 0, costUsd: 0 };
    row.totalTokens += event.totalTokens;
    row.costUsd += event.costUsd;
    rows.set(key, row);
  }
  return [...rows.values()].sort((a, b) => `${a.cli}:${a.toolName}`.localeCompare(`${b.cli}:${b.toolName}`));
}

function summarizeControls(events: BudgetEvent[]): Array<{ controlKind: string; count: number }> {
  const rows = new Map<string, number>();
  for (const event of events) {
    const key = event.controlKind ?? "unknown";
    rows.set(key, (rows.get(key) ?? 0) + 1);
  }
  return [...rows.entries()]
    .map(([controlKind, count]) => ({ controlKind, count }))
    .sort((a, b) => a.controlKind.localeCompare(b.controlKind));
}

function stripUndefined<T extends Record<string, unknown>>(value: T): T {
  return Object.fromEntries(Object.entries(value).filter(([, entry]) => entry !== undefined)) as T;
}

interface ParsedCli {
  command: "check" | "record" | "control" | "weekly-report";
  options: RecordBudgetEventOptions & CheckBudgetOptions & Partial<BudgetControlOptions> & WeeklyBudgetReportOptions;
}

function parseArgs(argv: string[]): ParsedCli {
  const command = argv.shift();
  if (command !== "check" && command !== "record" && command !== "control" && command !== "weekly-report") {
    throw new Error("uso: budget-tracker <check|record|control|weekly-report> [opcoes]");
  }
  const options: RecordBudgetEventOptions & CheckBudgetOptions & Partial<BudgetControlOptions> & WeeklyBudgetReportOptions = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];
    const requireValue = (): string => {
      if (!next) throw new Error(`${arg} exige valor`);
      i += 1;
      return next;
    };
    if (arg === "--workspace") options.root = requireValue();
    else if (arg === "--now") options.now = parseDateArg(arg, requireValue());
    else if (arg === "--cli") options.cli = parseCliName(requireValue());
    else if (arg === "--hook") options.hook = parseHookName(requireValue());
    else if (arg === "--tool") options.toolName = requireValue();
    else if (arg === "--task-id") options.taskId = requireValue();
    else if (arg === "--pr-id") options.prId = requireValue();
    else if (arg === "--control-kind") options.controlKind = parseControlKind(requireValue());
    else if (arg === "--tier") options.tier = parseTier(requireValue());
    else if (arg === "--resource-id") options.resourceId = requireValue();
    else if (arg === "--status") options.status = parseControlStatus(requireValue());
    else if (arg === "--file") options.filePath = requireValue();
    else if (arg === "--branch") options.branch = requireValue();
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

function parseDateArg(name: string, value: string): Date {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) throw new Error(`${name} invalido: ${value}`);
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

function parseControlKind(value: string): BudgetControlKind {
  const allowed: BudgetControlKind[] = [
    "concurrency",
    "tool_error",
    "file_edit",
    "regulatory_failure",
    "tenancy_failure",
    "hash_chain_divergence",
    "worktree_heartbeat",
  ];
  if (allowed.includes(value as BudgetControlKind)) return value as BudgetControlKind;
  throw new Error(`--control-kind invalido: ${value}`);
}

function parseTier(value: string): BudgetTier {
  if (value === "tier1" || value === "tier2" || value === "tier3") return value;
  throw new Error(`--tier invalido: ${value}`);
}

function parseControlStatus(value: string): BudgetControlStatus {
  if (value === "start" || value === "finish" || value === "failure" || value === "success") return value;
  throw new Error(`--status invalido: ${value}`);
}

function requireControlOptions(options: ParsedCli["options"]): BudgetControlOptions {
  if (!options.controlKind) throw new Error("--control-kind exige valor");
  if (!options.resourceId) throw new Error("--resource-id exige valor");
  if (!options.status) throw new Error("--status exige valor");
  return {
    ...options,
    controlKind: options.controlKind,
    resourceId: options.resourceId,
    status: options.status,
  };
}

function main(): void {
  try {
    const parsed = parseArgs(process.argv.slice(2));
    if (parsed.command === "record") {
      const { event, path } = recordBudgetEvent(parsed.options);
      console.log(`budget-tracker: recorded ${event.totalTokens} tokens, $${event.costUsd.toFixed(4)} in ${path}`);
      return;
    }

    if (parsed.command === "control") {
      const controlOptions = requireControlOptions(parsed.options);
      const result = checkBudgetControls(controlOptions);
      for (const message of result.messages) console.log(message);
      if (result.blocked) {
        console.error("budget-tracker: circuit breaker excedido; bloqueando");
        process.exit(1);
      }
      const { event, path } = recordBudgetControlEvent(controlOptions);
      console.log(`budget-tracker: recorded control ${event.controlKind ?? "unknown"} in ${path}`);
      return;
    }

    if (parsed.command === "weekly-report") {
      const { path } = generateWeeklyBudgetReport(parsed.options);
      console.log(`budget-tracker: weekly report written to ${path}`);
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
