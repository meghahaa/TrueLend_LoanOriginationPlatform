#!/usr/bin/env node
// PreToolUse hook (Write|Edit|MultiEdit|Bash) — TrueLend NFR-02 / NFR-05.
// Blocks modification or deletion of EXISTING policy versions and SQL migrations.
// Creating a NEW policies/loan_policy.vNNN.json or migrations/NNN_*.sql is allowed.
// Exit 2 = block (stderr is shown to the agent). Any internal error fails open (exit 0).
const fs = require('fs');
const path = require('path');

const PROTECTED = [
  /(^|\/)policies\/loan_policy\.v\d+\.json$/,
  /(^|\/)migrations\/[^/]+\.sql$/,
];
const isProtected = (p) => PROTECTED.some((re) => re.test(p.replace(/\\/g, '/')));

function block(msg) {
  process.stderr.write(`BLOCKED by policy-immutability-check: ${msg}\n` +
    'Policy versions and migrations are append-only (NFR-02/05). Create a NEW file ' +
    '(next policy version number / next migration number) instead of editing or deleting. ' +
    'Use /new-policy-version for policy changes.\n');
  process.exit(2);
}

let raw = '';
process.stdin.on('data', (d) => (raw += d));
process.stdin.on('end', () => {
  let input;
  try { input = JSON.parse(raw || '{}'); } catch { process.exit(0); }
  const tool = input.tool_name || '';
  const ti = input.tool_input || {};
  const cwd = input.cwd || process.cwd();

  if (['Write', 'Edit', 'MultiEdit'].includes(tool) && ti.file_path) {
    const abs = path.resolve(cwd, ti.file_path.replace(/\\/g, '/'));
    if (isProtected(abs) && fs.existsSync(abs)) {
      block(`${ti.file_path} already exists and is protected.`);
    }
    process.exit(0);
  }

  if (tool === 'Bash' && typeof ti.command === 'string') {
    const cmd = ti.command;
    const touches = /(policies\/loan_policy\.v\d+\.json|migrations\/[^\s"']+\.sql)/.test(cmd.replace(/\\/g, '/'));
    const mutating = /(\brm\b|\bmv\b|\bsed\s+-i|\btruncate\b|\bgit\s+(checkout|restore|rm)\b|>\s*\S|\btee\b|\bperl\s+-i)/.test(cmd);
    // Allow creating new files via redirect only if the target does not exist yet.
    if (touches && mutating) {
      const m = cmd.replace(/\\/g, '/').match(/(policies\/loan_policy\.v\d+\.json|migrations\/[^\s"']+\.sql)/g) || [];
      const anyExisting = m.some((p) => fs.existsSync(path.resolve(cwd, p)));
      const destructive = /(\brm\b|\bmv\b|\bsed\s+-i|\btruncate\b|\bgit\s+(checkout|restore|rm)\b|\bperl\s+-i)/.test(cmd);
      if (destructive || anyExisting) block('shell command would modify/delete a protected file.');
    }
  }
  process.exit(0);
});
