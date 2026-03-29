import { readFile } from "node:fs/promises";
import path from "node:path";

export const dynamic = 'force-static';

export async function GET() {
  const promptPath = path.join(process.cwd(), "src", "prompts", "Role.md");
  const prompt = await readFile(promptPath, "utf8");

  return new Response(prompt, {
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}