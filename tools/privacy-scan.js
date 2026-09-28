// Check tracked project files only; don't traverse submodules or local state.
// This heuristic is an aid to review, not a guarantee that a tree is secret-free.
const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const root = path.resolve(process.argv[2] || '.');
const files = execFileSync('git', ['ls-files', '-z'], {cwd: root, encoding: 'utf8'}).split('\0').filter(Boolean);
const patterns = [
  ['private key', /-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----/],
  ['GitHub token', /\bgh[pousr]_[A-Za-z0-9]{30,}\b/],
  ['local identity file', /^(?:device\.json|adi\.pb)$/],
];
let findings = 0;
for (const file of files) {
  const full = path.join(root, file);
  if (!fs.statSync(full).isFile()) continue;
  if (/(?:^|\/)(?:\.env|device\.json|adi\.pb)$|\.(?:pem|key|plist)$/.test(file)) {
    console.error(`BLOCK: sensitive file type: ${file}`); findings++;
  }
  const lines = fs.readFileSync(full, 'utf8').split(/\r?\n/);
  for (const [index, line] of lines.entries()) {
    for (const [name, pattern] of patterns.slice(0, 2)) {
      if (pattern.test(line)) {
        // Never print a possible secret itself.
        console.error(`BLOCK: ${name}: ${file}:${index + 1}`); findings++;
      }
    }
  }
}
console.log(`Checked ${files.length} tracked paths; ${findings} blocking findings.`);
process.exitCode = findings ? 1 : 0;
