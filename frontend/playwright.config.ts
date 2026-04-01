import { defineConfig, devices } from "@playwright/test";
import fs from "fs";
import path from "path";

function loadEnvFile(filePath: string): Record<string, string> {
  if (!fs.existsSync(filePath)) {
    return {};
  }

  const env: Record<string, string> = {};
  const contents = fs.readFileSync(filePath, "utf8");

  for (const rawLine of contents.split("\n")) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }

    const separatorIndex = line.indexOf("=");
    if (separatorIndex <= 0) {
      continue;
    }

    const key = line.slice(0, separatorIndex).trim();
    let value = line.slice(separatorIndex + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    env[key] = value;
  }

  return env;
}

const repoRoot = path.resolve(__dirname, "..");
const includeRootEnv = process.env.PLAYWRIGHT_INCLUDE_ROOT_ENV === "true";
const frontendEnv = loadEnvFile(path.join(__dirname, ".env.local"));
const backendEnv = loadEnvFile(path.join(repoRoot, "backend/.env"));
const rootEnv = includeRootEnv ? loadEnvFile(path.join(repoRoot, ".env.local")) : {};
const rawEnv = {
  ...rootEnv,
  ...frontendEnv,
  ...backendEnv,
  ...process.env,
};

const frontendHost = rawEnv.PLAYWRIGHT_FRONTEND_HOST ?? "127.0.0.1";
const frontendPort = rawEnv.PLAYWRIGHT_FRONTEND_PORT ?? "3000";
const backendHost = rawEnv.PLAYWRIGHT_BACKEND_HOST ?? "127.0.0.1";
const backendPort = rawEnv.PLAYWRIGHT_BACKEND_PORT ?? "8000";
const frontendBaseUrl =
  rawEnv.PLAYWRIGHT_BASE_URL ?? `http://${frontendHost}:${frontendPort}`;
const backendBaseUrl =
  rawEnv.PLAYWRIGHT_BACKEND_URL ??
  rawEnv.NEXT_PUBLIC_BACKEND_URL ??
  `http://${backendHost}:${backendPort}`;
const backendHealthUrl =
  rawEnv.PLAYWRIGHT_BACKEND_HEALTH_URL ?? `${backendBaseUrl.replace(/\/$/, "")}/health`;

const sharedEnv = {
  ...rawEnv,
  NEXT_PUBLIC_BACKEND_URL: backendBaseUrl,
  SUPABASE_URL: rawEnv.SUPABASE_URL ?? frontendEnv.NEXT_PUBLIC_SUPABASE_URL ?? "",
  SUPABASE_ANON_KEY: rawEnv.SUPABASE_ANON_KEY ?? frontendEnv.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "",
};

// Keep frontend/.env.local as the default source of truth for Playwright and the
// local Next.js app. Root .env.local is reserved for repo/Vercel concerns and is
// only loaded here when PLAYWRIGHT_INCLUDE_ROOT_ENV=true is set intentionally.

Object.assign(process.env, sharedEnv);

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  timeout: 240_000,
  expect: {
    timeout: 30_000,
  },
  use: {
    baseURL: frontendBaseUrl,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: [
    {
      command: `cd "${repoRoot}" && python3 -m uvicorn backend.main:app --host ${backendHost} --port ${backendPort}`,
      url: backendHealthUrl,
      reuseExistingServer: false,
      stdout: "pipe",
      stderr: "pipe",
      env: sharedEnv,
    },
    {
      command: `cd "${__dirname}" && npm run dev -- --hostname ${frontendHost} --port ${frontendPort}`,
      url: frontendBaseUrl,
      reuseExistingServer: false,
      stdout: "pipe",
      stderr: "pipe",
      env: sharedEnv,
    },
  ],
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
      },
    },
  ],
});
