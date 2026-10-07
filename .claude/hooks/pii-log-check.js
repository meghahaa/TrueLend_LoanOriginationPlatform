#!/usr/bin/env node
// PostToolUse hook (Write|Edit|MultiEdit) — TrueLend NFR-03.
// Flags log/print statements that mention sensitive identifiers (PAN, Aadhaar, salary/document content).
// Escape hatch (e.g. logging the *word* in a message that carries no value): append "# pii-ok".
const fs = require('fs');
const path = require('path');

const SCOPE = /(^|\/)src\/.+\.py$/;
const LOG_CALL = /(\b(logger|logging|log|LOG)\.(debug|info|warning|warn|error|exception|critical)\s*\(|\bprint\s*\()/;
const SENSITIVE = /\b(pan|aadhaar|aadhar|salary_?doc\w*|salary_?slip_?content|document_?content|file_?content|raw_?body)\b/i;

let raw = '';
process.stdin.on('data', (d) => (raw += d));
process.stdin.on('end', () => {
  let input;
  try { input = JSON.parse(raw || '{}'); } catch { process.exit(0); }
  const fp = (input.tool_input || {}).file_path;
  if (!fp || !SCOPE.test(fp.replace(/\\/g, '/'))) process.exit(0);
  let text;
  try { text = fs.readFileSync(path.resolve(input.cwd || process.cwd(), fp.replace(/\\/g, '/')), 'utf8'); } catch { process.exit(0); }

  const hits = [];
  text.split(/\r?\n/).forEach((line, i) => {
    if (/#\s*pii-ok/.test(line)) return;
    if (LOG_CALL.test(line) && SENSITIVE.test(line)) hits.push(`${fp}:${i + 1}  ${line.trim().slice(0, 100)}`);
  });
  if (hits.length) {
    process.stderr.write('pii-log-check (NFR-03): sensitive identifier in a log/print call.\n' +
      hits.slice(0, 10).join('\n') +
      '\nLog ids and reason codes only. Never log PAN, Aadhaar or document content.\n');
    process.exit(2);
  }
  process.exit(0);
});
