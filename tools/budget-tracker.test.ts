import assert from "node:assert/strict";
import { existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";

import {
  checkBudget,
  checkBudgetControls,
  generateWeeklyBudgetReport,
  recordBudgetControlEvent,
  recordBudgetEvent,
} from "./budget-tracker";

const repoRoot = process.cwd();
const scriptPath = join(repoRoot, "tools", "budget-tracker.ts");
const tsxLoaderUrl = pathToFileURL(join(repoRoot, "node_modules", "tsx", "dist", "loader.mjs")).href;

function makeWorkspace(): { root: string; cleanup: () => void } {
  const root = mkdtempSync(join(tmpdir(), "afere-budget-"));
  mkdirSync(join(root, ".claude"), { recursive: true });
  writeFileSync(
    join(root, ".claude", "settings.json"),
    JSON.stringify({
      budgets: {
        tokens: {
          perToolCallSoft: 20_000,
          perToolCallHard: 50_000,
          perTaskSoft: 100_000,
          perTaskHard: 200_000,
          perPrSoft: 350_000,
          perPrHard: 500_000,
          contextRotSoft: 300_000,
          contextRotHard: 400_000,
        },
        costUSD: {
          perDevPerDaySoft: 15,
          perDevPerDayHard: 30,
          perDevPerWeekSoft: 60,
          perDevPerWeekHard: 120,
          perPrSoft: 8,
          perPrHard: 15,
          perCloudTaskSoft: 3,
          perCloudTaskHard: 5,
        },
        concurrency: {
          tier1Subagents: 5,
          tier2Worktrees: 3,
          tier3CloudAgents: 2,
        },
        circuitBreakers: {
          consecutiveToolErrors: 3,
          sameFileEdits: 5,
          sameFileEditWindowMinutes: 10,
          regulatoryFailures: 2,
          tenancyFailures: 1,
          hashChainDivergences: 1,
          worktreeHeartbeatHours: 4,
        },
      },
    }),
  );
  return {
    root,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

test("records budget consumption as dated JSONL", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const result = recordBudgetEvent({
      root,
      now: new Date("2026-04-20T12:00:00.000Z"),
      cli: "claude",
      hook: "PostToolUse",
      toolName: "Bash",
      inputTokens: 120,
      outputTokens: 80,
      costUsd: 0.0125,
      taskId: "task-a",
      prId: "PR-7",
    });

    assert.equal(result.path.replace(/\\/g, "/").endsWith("compliance/budget-log/2026-04-20.jsonl"), true);
    const lines = readFileSync(result.path, "utf8").trim().split("\n");
    assert.equal(lines.length, 1);
    assert.deepEqual(JSON.parse(lines[0] ?? "{}"), {
      version: 1,
      ts: "2026-04-20T12:00:00.000Z",
      date: "2026-04-20",
      type: "consumption",
      cli: "claude",
      hook: "PostToolUse",
      toolName: "Bash",
      taskId: "task-a",
      prId: "PR-7",
      inputTokens: 120,
      outputTokens: 80,
      totalTokens: 200,
      costUsd: 0.0125,
      metadataMissing: false,
    });
  } finally {
    cleanup();
  }
});

test("blocks when a daily hard cost cap would be exceeded", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    recordBudgetEvent({
      root,
      now: new Date("2026-04-20T08:00:00.000Z"),
      cli: "claude",
      hook: "PostToolUse",
      toolName: "Bash",
      costUsd: 29.5,
    });

    const result = checkBudget({
      root,
      now: new Date("2026-04-20T12:00:00.000Z"),
      currentCostUsd: 0.75,
    });

    assert.equal(result.blocked, true);
    assert.match(result.messages.join("\n"), /BUDGET-USD-DAY-HARD/);
    assert.match(result.messages.join("\n"), /30/);
  } finally {
    cleanup();
  }
});

test("warns but does not block when PR token soft cap is exceeded below hard cap", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    recordBudgetEvent({
      root,
      now: new Date("2026-04-20T08:00:00.000Z"),
      cli: "codex",
      hook: "PostToolUse",
      toolName: "shell",
      inputTokens: 220_000,
      outputTokens: 120_000,
      prId: "PR-8",
    });

    const result = checkBudget({
      root,
      now: new Date("2026-04-20T12:00:00.000Z"),
      currentTotalTokens: 20_000,
      prId: "PR-8",
    });

    assert.equal(result.blocked, false);
    assert.match(result.messages.join("\n"), /BUDGET-TOKENS-PR-SOFT/);
    assert.doesNotMatch(result.messages.join("\n"), /BUDGET-TOKENS-PR-HARD/);
  } finally {
    cleanup();
  }
});

test("does not count previous alert events as budget consumption", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    recordBudgetEvent({
      root,
      now: new Date("2026-04-20T08:00:00.000Z"),
      cli: "codex",
      hook: "PostToolUse",
      toolName: "shell",
      totalTokens: 340_000,
      prId: "PR-9",
    });

    const firstCheck = checkBudget({
      root,
      now: new Date("2026-04-20T09:00:00.000Z"),
      currentTotalTokens: 20_000,
      prId: "PR-9",
      writeEvents: true,
    });
    assert.equal(firstCheck.blocked, false);
    assert.match(firstCheck.messages.join("\n"), /BUDGET-TOKENS-PR-SOFT/);

    const secondCheck = checkBudget({
      root,
      now: new Date("2026-04-20T10:00:00.000Z"),
      prId: "PR-9",
    });

    assert.equal(secondCheck.blocked, false);
    assert.equal(secondCheck.messages.join("\n"), "");
  } finally {
    cleanup();
  }
});

test("does not persist alert events unless requested by a hook", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const recorded = recordBudgetEvent({
      root,
      now: new Date("2026-04-20T08:00:00.000Z"),
      cli: "codex",
      hook: "PostToolUse",
      toolName: "shell",
      totalTokens: 340_000,
      prId: "PR-10",
    });

    const result = checkBudget({
      root,
      now: new Date("2026-04-20T09:00:00.000Z"),
      currentTotalTokens: 20_000,
      prId: "PR-10",
    });

    assert.equal(result.blocked, false);
    assert.match(result.messages.join("\n"), /BUDGET-TOKENS-PR-SOFT/);
    assert.equal(readFileSync(recorded.path, "utf8").trim().split("\n").length, 1);
  } finally {
    cleanup();
  }
});

test("blocks when tier 1 concurrency would exceed the configured cap", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    for (let index = 1; index <= 5; index += 1) {
      recordBudgetControlEvent({
        root,
        now: new Date(`2026-04-20T08:0${index}:00.000Z`),
        controlKind: "concurrency",
        tier: "tier1",
        resourceId: `agent-${index}`,
        status: "start",
      });
    }

    const result = checkBudgetControls({
      root,
      now: new Date("2026-04-20T08:10:00.000Z"),
      controlKind: "concurrency",
      tier: "tier1",
      resourceId: "agent-6",
      status: "start",
    });

    assert.equal(result.blocked, true);
    assert.match(result.messages.join("\n"), /BUDGET-CONCURRENCY-TIER1-HARD/);
    assert.match(result.messages.join("\n"), /6\/5/);
  } finally {
    cleanup();
  }
});

test("blocks after three consecutive tool errors in the same task", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    for (let index = 1; index <= 2; index += 1) {
      recordBudgetControlEvent({
        root,
        now: new Date(`2026-04-20T09:0${index}:00.000Z`),
        controlKind: "tool_error",
        resourceId: `tool-error-${index}`,
        status: "failure",
        taskId: "task-loop",
      });
    }

    const result = checkBudgetControls({
      root,
      now: new Date("2026-04-20T09:03:00.000Z"),
      controlKind: "tool_error",
      resourceId: "tool-error-3",
      status: "failure",
      taskId: "task-loop",
    });

    assert.equal(result.blocked, true);
    assert.match(result.messages.join("\n"), /BUDGET-CIRCUIT-TOOL-ERRORS-HARD/);
    assert.match(result.messages.join("\n"), /3\/3/);
  } finally {
    cleanup();
  }
});

test("blocks after five edits to the same file within ten minutes", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    for (let index = 1; index <= 4; index += 1) {
      recordBudgetControlEvent({
        root,
        now: new Date(`2026-04-20T10:0${index}:00.000Z`),
        controlKind: "file_edit",
        resourceId: `edit-${index}`,
        status: "success",
        filePath: "tools/budget-tracker.ts",
      });
    }

    const result = checkBudgetControls({
      root,
      now: new Date("2026-04-20T10:05:00.000Z"),
      controlKind: "file_edit",
      resourceId: "edit-5",
      status: "success",
      filePath: "tools/budget-tracker.ts",
    });

    assert.equal(result.blocked, true);
    assert.match(result.messages.join("\n"), /BUDGET-CIRCUIT-FILE-EDITS-HARD/);
    assert.match(result.messages.join("\n"), /5\/5/);
  } finally {
    cleanup();
  }
});

test("blocks after two regulatory eval failures in the same branch", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    recordBudgetControlEvent({
      root,
      now: new Date("2026-04-20T11:01:00.000Z"),
      controlKind: "regulatory_failure",
      resourceId: "regulatory-1",
      status: "failure",
      branch: "codex/p0-7-budget-controls",
    });

    const result = checkBudgetControls({
      root,
      now: new Date("2026-04-20T11:02:00.000Z"),
      controlKind: "regulatory_failure",
      resourceId: "regulatory-2",
      status: "failure",
      branch: "codex/p0-7-budget-controls",
    });

    assert.equal(result.blocked, true);
    assert.match(result.messages.join("\n"), /BUDGET-CIRCUIT-REGULATORY-HARD/);
    assert.match(result.messages.join("\n"), /2\/2/);
  } finally {
    cleanup();
  }
});

test("blocks immediately on a tenancy eval failure", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const result = checkBudgetControls({
      root,
      now: new Date("2026-04-20T12:00:00.000Z"),
      controlKind: "tenancy_failure",
      resourceId: "tenancy-1",
      status: "failure",
      branch: "codex/p0-7-budget-controls",
    });

    assert.equal(result.blocked, true);
    assert.match(result.messages.join("\n"), /BUDGET-CIRCUIT-TENANCY-HARD/);
    assert.match(result.messages.join("\n"), /1\/1/);
  } finally {
    cleanup();
  }
});

test("blocks immediately on audit hash-chain divergence", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    const result = checkBudgetControls({
      root,
      now: new Date("2026-04-20T12:30:00.000Z"),
      controlKind: "hash_chain_divergence",
      resourceId: "audit-log-2026-04-20",
      status: "failure",
    });

    assert.equal(result.blocked, true);
    assert.match(result.messages.join("\n"), /BUDGET-CIRCUIT-HASH-CHAIN-HARD/);
    assert.match(result.messages.join("\n"), /1\/1/);
  } finally {
    cleanup();
  }
});

test("alerts when a worktree heartbeat is older than four hours", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    recordBudgetControlEvent({
      root,
      now: new Date("2026-04-20T08:00:00.000Z"),
      controlKind: "worktree_heartbeat",
      resourceId: "worktree-a",
      status: "success",
    });

    const result = checkBudgetControls({
      root,
      now: new Date("2026-04-20T12:01:00.000Z"),
      controlKind: "worktree_heartbeat",
      resourceId: "heartbeat-scan",
      status: "success",
    });

    assert.equal(result.blocked, false);
    assert.match(result.messages.join("\n"), /BUDGET-CIRCUIT-WORKTREE-HEARTBEAT-SOFT/);
    assert.match(result.messages.join("\n"), /worktree-a/);
  } finally {
    cleanup();
  }
});

test("generates a weekly budget report with consumption and control totals", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    recordBudgetEvent({
      root,
      now: new Date("2026-04-20T08:00:00.000Z"),
      cli: "claude",
      hook: "PostToolUse",
      toolName: "Bash",
      totalTokens: 200,
      costUsd: 0.75,
    });
    recordBudgetEvent({
      root,
      now: new Date("2026-04-21T08:00:00.000Z"),
      cli: "codex",
      hook: "PostToolUse",
      toolName: "shell_command",
      totalTokens: 100,
      costUsd: 0.5,
    });
    recordBudgetControlEvent({
      root,
      now: new Date("2026-04-21T09:00:00.000Z"),
      controlKind: "tool_error",
      resourceId: "tool-error-1",
      status: "failure",
      taskId: "task-report",
    });

    const report = generateWeeklyBudgetReport({
      root,
      now: new Date("2026-04-22T12:00:00.000Z"),
    });

    assert.equal(report.path.replace(/\\/g, "/").endsWith("compliance/budget-log/weekly/2026-W17.md"), true);
    assert.match(report.content, /# Budget semanal 2026-W17/);
    assert.match(report.content, /Total tokens: 300/);
    assert.match(report.content, /Total cost USD: 1\.2500/);
    assert.match(report.content, /\| claude \| Bash \| 200 \| 0\.7500 \|/);
    assert.match(report.content, /\| tool_error \| 1 \|/);
  } finally {
    cleanup();
  }
});

test("CLI weekly-report writes the report file", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    recordBudgetEvent({
      root,
      now: new Date("2026-04-20T08:00:00.000Z"),
      cli: "claude",
      hook: "PostToolUse",
      toolName: "Bash",
      totalTokens: 200,
      costUsd: 0.75,
    });

    const result = spawnSync(
      process.execPath,
      ["--import", tsxLoaderUrl, scriptPath, "weekly-report", "--workspace", root, "--now", "2026-04-22T12:00:00.000Z"],
      { cwd: repoRoot, encoding: "utf8" },
    );

    const path = join(root, "compliance", "budget-log", "weekly", "2026-W17.md");
    assert.equal(result.status, 0, result.stdout + result.stderr);
    assert.equal(existsSync(path), true);
    assert.match(readFileSync(path, "utf8"), /Total tokens: 200/);
  } finally {
    cleanup();
  }
});

test("CLI control blocks a concurrency hard-cap violation", () => {
  const { root, cleanup } = makeWorkspace();
  try {
    for (let index = 1; index <= 5; index += 1) {
      recordBudgetControlEvent({
        root,
        now: new Date(`2026-04-20T08:0${index}:00.000Z`),
        controlKind: "concurrency",
        tier: "tier1",
        resourceId: `agent-${index}`,
        status: "start",
      });
    }

    const result = spawnSync(
      process.execPath,
      [
        "--import",
        tsxLoaderUrl,
        scriptPath,
        "control",
        "--workspace",
        root,
        "--control-kind",
        "concurrency",
        "--tier",
        "tier1",
        "--resource-id",
        "agent-6",
        "--status",
        "start",
      ],
      { cwd: repoRoot, encoding: "utf8" },
    );

    assert.equal(result.status, 1);
    assert.match(result.stdout + result.stderr, /BUDGET-CONCURRENCY-TIER1-HARD/);
  } finally {
    cleanup();
  }
});
