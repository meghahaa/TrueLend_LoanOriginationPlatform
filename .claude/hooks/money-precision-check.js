#!/usr/bin/env node
// PostToolUse hook (Write|Edit|MultiEdit) — TrueLend NFR-01.
// Flags floating-point usage in money-handling backend code (src/domain, src/services, src/repositories).
// Escape hatch for genuinely non-money floats: append "# float-ok" to the line.
// Exit 2 = feed the message back to the agent so it fixes the file. Errors fail open.
const fs = require('fs');
const path = require('path');

const SCOPE = /(^|\/)src\/(domain|services|repositories)\/.+\.py$/;
const RULES = [
  [/\bfloat\s*\(/, 'float() call'],
  [/(:|->)\s*float\b/, 'float type annotation'],
  [/\bDecimal\s*\(\s*-?\d+\.\d+\s*\)/, 'Decimal built from a float literal — use a string: Decimal("0.1")'],
  [/\bround\s*\(/, 'built-in round() — use Decimal.quantize(..., ROUND_HALF_UP)'],
  [/\bmath\.(pow|exp|log)\b/, 'math.* returns float — use Decimal arithmetic'],
];

let raw = '';
process.stdin.on('data', (d) => (raw += d));
process.stdin.on('end', () => {
  let input;
  try { input = JSON.parse(raw || '{}'); } catch { process.exit(0); }
  const fp = (input.tool_input || {}).file_path;
  if (!fp) process.exit(0);
  const norm = fp.replace(/\\/g, '/');
  if (!SCOPE.test(norm)) process.exit(0);
  let text;
  try { text = fs.readFileSync(path.resolve(input.cwd || process.cwd(), fp.replace(/\\/g, '/')), 'utf8'); } catch { process.exit(0); }

  const hits = [];
  text.split(/\r?\n/).forEach((line, i) => {
    const code = line.split('#')[0];
    if (/#\s*float-ok/.test(line) || !code.trim()) return;
    for (const [re, label] of RULES) if (re.test(code)) hits.push(`${fp}:${i + 1}  ${label}`);
  });
  if (hits.length) {
    process.stderr.write('money-precision-check (NFR-01): floating-point in money code.\n' +
      hits.slice(0, 10).join('\n') +
      '\nUse decimal.Decimal built from str/int, quantize to 2 dp with ROUND_HALF_UP.\n');
    process.exit(2);
  }
  process.exit(0);
});
