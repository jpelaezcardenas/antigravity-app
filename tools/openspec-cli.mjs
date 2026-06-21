import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const repoRoot = path.resolve(process.cwd());
const openspecRoot = path.join(repoRoot, 'openspec');
const changesRoot = path.join(openspecRoot, 'changes');

function exists(p) {
  try {
    return fs.existsSync(p);
  } catch {
    return false;
  }
}

function readText(p) {
  return fs.readFileSync(p, 'utf8');
}

function listChangeDirs() {
  if (!exists(changesRoot)) return [];
  return fs
    .readdirSync(changesRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name !== 'archive')
    .map((entry) => entry.name)
    .sort((a, b) => a.localeCompare(b));
}

function parseSimpleYaml(text) {
  const result = {};
  const lines = text.split(/\r?\n/);
  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    const idx = line.indexOf(':');
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    const value = line.slice(idx + 1).trim();
    result[key] = value.replace(/^['"]|['"]$/g, '');
  }
  return result;
}

function printList(json = false) {
  const changes = listChangeDirs().map((name) => {
    const dir = path.join(changesRoot, name);
    const metaPath = path.join(dir, '.openspec.yaml');
    const proposal = path.join(dir, 'proposal.md');
    const design = path.join(dir, 'design.md');
    const tasks = path.join(dir, 'tasks.md');
    const meta = exists(metaPath) ? parseSimpleYaml(readText(metaPath)) : {};
    return {
      name,
      path: path.relative(repoRoot, dir).replace(/\\/g, '/'),
      schema: meta.schema || null,
      proposal: exists(proposal),
      design: exists(design),
      tasks: exists(tasks),
    };
  });

  if (json) {
    process.stdout.write(JSON.stringify({ changes }, null, 2) + '\n');
    return;
  }

  if (changes.length === 0) {
    console.log('No active OpenSpec changes.');
    return;
  }

  for (const change of changes) {
    console.log(`${change.name}\t${change.path}`);
  }
}

function validateAll(json = false, strict = false) {
  const errors = [];
  const warnings = [];

  if (!exists(openspecRoot)) {
    errors.push('openspec/ directory is missing');
  }

  const configPath = path.join(openspecRoot, 'config.yaml');
  if (!exists(configPath)) {
    errors.push('openspec/config.yaml is missing');
  }

  const changes = listChangeDirs();
  for (const name of changes) {
    const dir = path.join(changesRoot, name);
    const metaPath = path.join(dir, '.openspec.yaml');
    const proposal = path.join(dir, 'proposal.md');
    const design = path.join(dir, 'design.md');
    const tasks = path.join(dir, 'tasks.md');
    if (!exists(metaPath)) errors.push(`${name}: missing .openspec.yaml`);
    if (!exists(proposal)) errors.push(`${name}: missing proposal.md`);
    if (!exists(design)) errors.push(`${name}: missing design.md`);
    if (!exists(tasks)) errors.push(`${name}: missing tasks.md`);
  }

  if (strict) {
    const repoFiles = [
      path.join(repoRoot, 'specs', 'bunker-social-ops-retoma-2026-05-28.md'),
      ...changes.flatMap((name) => [
        path.join(openspecRoot, 'changes', name, 'proposal.md'),
        path.join(openspecRoot, 'changes', name, 'design.md'),
        path.join(openspecRoot, 'changes', name, 'tasks.md'),
      ]),
    ];
    for (const file of repoFiles) {
      if (!exists(file)) errors.push(`strict: missing required file ${path.relative(repoRoot, file)}`);
    }
  }

  const output = {
    ok: errors.length === 0,
    errors,
    warnings,
    checked: {
      openspecRoot: path.relative(repoRoot, openspecRoot).replace(/\\/g, '/'),
      changes: changes.length,
      strict,
    },
  };

  if (json) {
    process.stdout.write(JSON.stringify(output, null, 2) + '\n');
  } else {
    if (output.ok) {
      console.log(`Validation OK (${changes.length} change(s) checked${strict ? ', strict' : ''})`);
    } else {
      console.log(`Validation failed: ${errors.length} error(s)`);
      for (const error of errors) console.log(`- ${error}`);
    }
  }

  process.exitCode = output.ok ? 0 : 1;
}

function main() {
  const args = process.argv.slice(2);
  const [cmd, ...rest] = args;
  const flags = new Set(rest.filter((arg) => arg.startsWith('--')));
  const hasJson = flags.has('--json');

  if (cmd === 'list') {
    printList(hasJson);
    return;
  }

  if (cmd === 'validate') {
    const all = flags.has('--all');
    const strict = flags.has('--strict');
    if (!all) {
      console.error('Only --all validation is supported by this local shim.');
      process.exit(1);
    }
    validateAll(hasJson, strict);
    return;
  }

  console.error(`Unsupported openspec command: ${cmd || '(none)'}`);
  process.exit(1);
}

main();
