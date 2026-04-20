import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const STATUS_PATH = "harness/STATUS.md";
const DASHBOARD_PATH = "compliance/harness-dashboard.md";
const COVERAGE_PATH = "compliance/validation-dossier/coverage-report.md";
const PRIORITIES = ["P0", "P1", "P2"] as const;

type Priority = (typeof PRIORITIES)[number];

export type HarnessDashboardItem = {
  id: string;
  priority: Priority;
  title: string;
  status: "proposed" | "approved" | "in_progress" | "implemented" | "rejected" | "unknown";
  statusText: string;
};

export type HarnessDashboard = {
  markdown: string;
  items: HarnessDashboardItem[];
};

export type HarnessDashboardCheck = {
  errors: string[];
  itemCount: number;
};

export function buildHarnessDashboard(root = process.cwd()): HarnessDashboard {
  const statusPath = resolve(root, STATUS_PATH);
  if (!existsSync(statusPath)) {
    throw new Error(`${STATUS_PATH} não encontrado.`);
  }

  const items = parseStatusItems(readFileSync(statusPath, "utf8"));
  const gates = parseCheckAllCommands(root);
  const coverage = parseCoverage(root);
  return {
    items,
    markdown: renderDashboard(items, gates, coverage),
  };
}

export function checkHarnessDashboard(root = process.cwd()): HarnessDashboardCheck {
  const expected = buildHarnessDashboard(root);
  const dashboardPath = resolve(root, DASHBOARD_PATH);
  const errors: string[] = [];

  if (!existsSync(dashboardPath)) {
    errors.push(`DASH-001: dashboard ausente: ${DASHBOARD_PATH}. Rode pnpm harness-dashboard:write.`);
    return { errors, itemCount: expected.items.length };
  }

  const current = normalizeGeneratedText(readFileSync(dashboardPath, "utf8"));
  if (current.trimEnd() !== expected.markdown.trimEnd()) {
    errors.push(`DASH-002: ${DASHBOARD_PATH} desatualizado. Rode pnpm harness-dashboard:write.`);
  }

  return { errors, itemCount: expected.items.length };
}

export function writeHarnessDashboard(root = process.cwd()): HarnessDashboard {
  const dashboard = buildHarnessDashboard(root);
  const dashboardPath = resolve(root, DASHBOARD_PATH);
  mkdirSync(dirname(dashboardPath), { recursive: true });
  writeFileSync(dashboardPath, dashboard.markdown);
  return dashboard;
}

function parseStatusItems(markdown: string): HarnessDashboardItem[] {
  const items: HarnessDashboardItem[] = [];
  let currentPriority: Priority | undefined;

  for (const rawLine of markdown.replace(/\r\n/g, "\n").split("\n")) {
    const heading = rawLine.match(/^##\s+(P[0-2])\b/);
    if (heading?.[1] && PRIORITIES.includes(heading[1] as Priority)) {
      currentPriority = heading[1] as Priority;
      continue;
    }

    if (!currentPriority || !rawLine.startsWith("| P")) continue;
    const cells = rawLine
      .split("|")
      .slice(1, -1)
      .map((cell) => cell.trim());
    if (cells.length < 4) continue;
    const [id, title, , statusText] = cells;
    if (!/^P[0-2]-\d+/.test(id)) continue;
    items.push({
      id,
      priority: currentPriority,
      title: stripMarkdown(title),
      status: normalizeStatus(statusText),
      statusText: stripMarkdown(statusText),
    });
  }

  return items;
}

function parseCheckAllCommands(root: string): string[] {
  const packagePath = resolve(root, "package.json");
  if (!existsSync(packagePath)) return [];
  const parsed = JSON.parse(readFileSync(packagePath, "utf8")) as { scripts?: Record<string, string> };
  const checkAll = parsed.scripts?.["check:all"] ?? "";
  return checkAll
    .split("&&")
    .map((command) => command.trim())
    .filter(Boolean)
    .map((command) => command.replace(/^pnpm\s+/, ""))
    .map((command) => command.replace(/^tsx\s+/, "tsx "))
    .filter(Boolean);
}

function parseCoverage(root: string) {
  const coveragePath = resolve(root, COVERAGE_PATH);
  const fallback = {
    total: 0,
    mapped: 0,
    validated: 0,
    missing: 0,
  };
  if (!existsSync(coveragePath)) return fallback;
  const text = readFileSync(coveragePath, "utf8");
  return {
    total: numberAfter(text, /Total de critérios:\s*(\d+)/),
    mapped: numberAfter(text, /Critérios com requisito mapeado:\s*(\d+)/),
    validated: numberAfter(text, /Critérios validados por teste ativo:\s*(\d+)/),
    missing: numberAfter(text, /Critérios sem requisito mapeado:\s*(\d+)/),
  };
}

function renderDashboard(
  items: HarnessDashboardItem[],
  gates: string[],
  coverage: { total: number; mapped: number; validated: number; missing: number },
) {
  const rows = PRIORITIES.map((priority) => {
    const scoped = items.filter((item) => item.priority === priority);
    return {
      priority,
      total: scoped.length,
      inProgress: scoped.filter((item) => item.status === "in_progress").length,
      implemented: scoped.filter((item) => item.status === "implemented").length,
      proposed: scoped.filter((item) => item.status === "proposed").length,
      rejected: scoped.filter((item) => item.status === "rejected").length,
    };
  });

  return [
    "# Harness Dashboard",
    "",
    "> Gerado por `pnpm harness-dashboard:write`. Não editar manualmente.",
    "",
    "## Status por Prioridade",
    "",
    "| Prioridade | Total | Em implementação | Implementado | Proposto/Não iniciado | Rejeitado |",
    "|------------|-------|------------------|--------------|------------------------|-----------|",
    ...rows.map(
      (row) =>
        `| ${row.priority} | ${row.total} | ${row.inProgress} | ${row.implemented} | ${row.proposed} | ${row.rejected} |`,
    ),
    "",
    "## Cobertura PRD §13",
    "",
    `- ${coverage.mapped}/${coverage.total} mapeados`,
    `- ${coverage.validated}/${coverage.total} validados por teste ativo`,
    `- ${coverage.missing}/${coverage.total} sem requisito mapeado`,
    "",
    "## Gates em check:all",
    "",
    ...gates.map((gate) => `- \`${gate}\``),
    "",
    "## Itens Abertos",
    "",
    ...items
      .filter((item) => item.status !== "implemented")
      .map((item) => `- ${item.id} (${item.priority}): ${item.title} — ${item.statusText}`),
    "",
  ].join("\n");
}

function normalizeStatus(statusText: string): HarnessDashboardItem["status"] {
  if (statusText.includes("[✓]")) return "implemented";
  if (statusText.includes("[~]")) return "in_progress";
  if (statusText.includes("[x]")) return "approved";
  if (statusText.includes("[!]")) return "rejected";
  if (statusText.includes("[ ]")) return "proposed";
  return "unknown";
}

function stripMarkdown(value: string) {
  return value
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/`/g, "")
    .trim();
}

function numberAfter(text: string, pattern: RegExp) {
  const match = text.match(pattern);
  return match?.[1] ? Number(match[1]) : 0;
}

function normalizeGeneratedText(text: string) {
  return text.replace(/\r\n/g, "\n");
}

function runCli() {
  const command = process.argv[2] ?? "check";
  if (command === "generate" || command === "write") {
    const dashboard = writeHarnessDashboard();
    console.log(`harness-dashboard: ${dashboard.items.length} item(ns) renderizados em ${DASHBOARD_PATH}.`);
    return 0;
  }

  if (command !== "check") {
    console.error("Uso: harness-dashboard [check|generate|write]");
    return 2;
  }

  const result = checkHarnessDashboard();
  console.log(`harness-dashboard: ${result.itemCount} item(ns) verificados.`);
  for (const error of result.errors) console.error(`ERROR ${error}`);
  return result.errors.length > 0 ? 1 : 0;
}

const isCli = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  process.exitCode = runCli();
}
