import path from "node:path";
import { fileURLToPath } from "node:url";

import dotenv from "dotenv";
import { defineConfig } from "drizzle-kit";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, "backend", ".env"), override: false });
dotenv.config({ path: path.join(__dirname, ".env.local"), override: false });

const url =
  process.env.DIRECT_URL ||
  process.env.SUPABASE_DB_URL ||
  process.env.DATABASE_URL;

if (!url) {
  throw new Error("DIRECT_URL or SUPABASE_DB_URL must be set for Drizzle migrations");
}

export default defineConfig({
  dialect: "postgresql",
  schema: "./drizzle/schema.ts",
  out: "./drizzle/migrations",
  dbCredentials: {
    url,
  },
  verbose: true,
  strict: true,
});
