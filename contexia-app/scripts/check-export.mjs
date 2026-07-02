#!/usr/bin/env node
/**
 * Static-export sanity check (OpenSpec reconcile-contexia-app-source-live-pwa, task 2.2 / 4.4).
 *
 * Fails the build pipeline if the export in out/ contains:
 *  - U+FFFD replacement characters (mojibake, e.g. "Cerrar Sesi�n")
 *  - double-encoded UTF-8 ("SesiÃ³n" style)
 *  - a localhost API base URL baked in (.env.local shadowing)
 * and verifies that:
 *  - the production API base URL is baked into the client chunks
 *  - "Cerrar Sesión" renders in the overview page HTML
 *
 * Usage: node scripts/check-export.mjs   (run from contexia-app/, after `npm run build`)
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const OUT_DIR = "out";
const PROD_API_HOST = "antigravity-app-production-175a.up.railway.app";
const CHECKED_EXTENSIONS = new Set([".html", ".js", ".css", ".txt", ".webmanifest", ".json"]);

function walk(dir, files = []) {
  for (const entry of readdirSync(dir)) {
    const fullPath = join(dir, entry);
    if (statSync(fullPath).isDirectory()) {
      walk(fullPath, files);
    } else if ([...CHECKED_EXTENSIONS].some((ext) => fullPath.endsWith(ext))) {
      files.push(fullPath);
    }
  }
  return files;
}

const errors = [];
let prodApiHostSeen = false;
let logoutLabelSeen = false;

const files = walk(OUT_DIR);
for (const file of files) {
  const text = readFileSync(file, "utf8");

  // U+FFFD inside a word (e.g. "Sesi�n") is mojibake; an isolated quoted "�"
  // is the URL polyfill's legitimate spec-mandated replacement literal.
  if (/[A-Za-z]�|�[A-Za-z]/.test(text)) {
    errors.push(`${file}: contains U+FFFD replacement character inside a word (mojibake)`);
  }
  if (/Ã[³©±­]/.test(text)) {
    errors.push(`${file}: contains double-encoded UTF-8 (e.g. "Ã³")`);
  }
  if (text.includes("localhost:8080") || text.includes("http://localhost")) {
    errors.push(`${file}: contains a localhost API URL — .env.local leaked into the build`);
  }
  if (text.includes(PROD_API_HOST)) {
    prodApiHostSeen = true;
  }
  if (file.endsWith("overview.html") && text.includes("Cerrar Sesión")) {
    logoutLabelSeen = true;
  }
}

if (!prodApiHostSeen) {
  errors.push(`no file in ${OUT_DIR}/ contains the production API host ${PROD_API_HOST}`);
}
if (!logoutLabelSeen) {
  errors.push(`out/app/overview.html does not contain a clean "Cerrar Sesión" label`);
}

if (errors.length > 0) {
  console.error(`check-export FAILED (${errors.length} problem(s)):`);
  for (const error of errors) console.error(`  - ${error}`);
  process.exit(1);
}

console.log(`check-export OK: ${files.length} files scanned, no mojibake, prod API baked, logout label clean.`);
