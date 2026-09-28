// Regenerate the standalone source directory from the provenance table.
// Usage: node tools/render-sources.js
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const provenance = fs.readFileSync(path.join(root, 'docs/provenance.md'), 'utf8');
const escape = value => value.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const rows = provenance.split(/\r?\n/).filter(line => line.startsWith('| ') && line.includes('https://github.com/')).map(line => {
  const cells = line.split('|').slice(1, -1).map(cell => cell.trim());
  const match = /^\[(https:\/\/github\.com\/[\w.-]+\/[\w.-]+)\]\(\1\)$/.exec(cells[1]);
  if (cells.length !== 3 || !match) throw new Error('Review changed provenance table format');
  const url = escape(match[1]);
  return `<tr><td>${escape(cells[0])}</td><td><a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a></td><td>${escape(cells[2])}</td></tr>`;
});
if (!rows.length) throw new Error('No source URLs found');
const html = `<!doctype html>
<html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AltServer-Linux — フォーク元・参照先 / Source directory</title>
<style>
body{font:16px/1.7 system-ui,sans-serif;color:#172b3a;background:#f5f7fa;max-width:1200px;margin:40px auto;padding:0 24px}
h1{font-size:1.65rem;line-height:1.4}p{max-width:80ch}.table{overflow-x:auto;background:white;border:1px solid #d8e0e7;border-radius:12px}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:14px 18px;border-bottom:1px solid #e5eaf0;vertical-align:top}th{background:#e8eff5}a{color:#075ba3;overflow-wrap:anywhere}a:focus-visible{outline:3px solid #bf6800;outline-offset:3px}td:first-child{min-width:180px}
</style>
<main><h1>フォーク元・参照先<br><span lang="en">AltServer-Linux source directory</span></h1>
<p>直接のフォーク元は NyaMisty の非公式 Linux 移植版です。公式実装、他者フォーク、設計の参考資料を区別しています。リンクは新しいタブで開きます。</p>
<p lang="en">The direct parent is NyaMisty's unofficial Linux port. Official source, third-party forks and design references are listed separately. Links open in a new tab.</p>
<div class="table"><table><thead><tr><th scope="col">役割 / Role</th><th scope="col">Repository URL</th><th scope="col">使用箇所 / Use</th></tr></thead><tbody>
${rows.join('\n')}
</tbody></table></div>
<p>詳細なコミットと採用理由 / Commits and decisions:
<a href="https://github.com/hinatamaxxx/AltServer-Linux/blob/new/docs/provenance.md" target="_blank" rel="noopener noreferrer">Provenance</a> ·
<a href="https://github.com/hinatamaxxx/AltServer-Linux/blob/new/docs/upstream-review.md" target="_blank" rel="noopener noreferrer">公式実装の調査 / Official-source review</a></p>
</main></html>
`;
fs.writeFileSync(path.join(root, 'docs/sources.html'), html);
console.log(`Rendered ${rows.length} source URLs with new-tab links.`);
