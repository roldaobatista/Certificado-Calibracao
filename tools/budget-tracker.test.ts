import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { checkBudget, recordBudgetEvent } from "./budget-tracker";

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
