/* Run the existing browser-script checks without npm dependencies. */
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const projectRoot = path.resolve(__dirname, '..');
const browserDirectory = path.join(projectRoot, 'src/limousine/presentation/web/static/web');
const testsDirectory = path.join(projectRoot, 'tests');
const browserScripts = fs
  .readdirSync(browserDirectory)
  .filter((name) => name.endsWith('.js'))
  .sort();
const testScripts = fs
  .readdirSync(testsDirectory)
  .filter((name) => name.endsWith('.cjs'))
  .sort();
let failures = 0;

function runNode(nodeArguments) {
  const result = spawnSync(process.execPath, nodeArguments, { cwd: projectRoot, stdio: 'inherit' });
  if (result.error || result.status !== 0) failures += 1;
}

for (const name of browserScripts) runNode(['--check', path.join(browserDirectory, name)]);
for (const name of testScripts) runNode([path.join(testsDirectory, name)]);

console.log(
  `${browserScripts.length} browser scripts and ${testScripts.length} frontend test files checked.`,
);
process.exitCode = failures ? 1 : 0;
