import { spawnSync } from "node:child_process";

const args = process.argv.slice(2);
const result = spawnSync(
  "pnpm",
  ["exec", "tsx", "apps/api/src/domain/emission/certificate-snapshots-tool.ts", ...args],
  {
    cwd: process.cwd(),
    stdio: "inherit",
    shell: process.platform === "win32",
  },
);

if (typeof result.status === "number") {
  process.exit(result.status);
}

process.exit(1);
