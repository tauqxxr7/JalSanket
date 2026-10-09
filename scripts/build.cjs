// Static frontend: no bundler or generated metrics. Copy reviewed assets only.
const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '..');
const output = path.join(root, 'dist');
fs.mkdirSync(output, {recursive:true});
fs.cpSync(path.join(root,'frontend'),output,{recursive:true});
for (const file of ['index.html','app.js','station.js','styles.css','assets/telemetry.svg','assets/environment.svg','assets/uncertain.svg','assets/insufficient.svg']) {
  if (!fs.statSync(path.join(output,file)).size) throw new Error(`Empty build artifact: ${file}`);
}
console.log('Built static frontend: 8 nonempty files. API remains a separate FastAPI service.');
