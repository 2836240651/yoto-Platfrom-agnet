/** Copy apps/web/dist → apps/workspace-desktop/web-dist for Electron packaging. */
const fs = require('fs')
const path = require('path')

const src = path.resolve(__dirname, '..', '..', 'web', 'dist')
const dest = path.resolve(__dirname, '..', 'web-dist')

function rm(p) {
  fs.rmSync(p, { recursive: true, force: true })
}

function copyDir(from, to) {
  fs.mkdirSync(to, { recursive: true })
  for (const name of fs.readdirSync(from)) {
    const a = path.join(from, name)
    const b = path.join(to, name)
    if (fs.statSync(a).isDirectory()) copyDir(a, b)
    else fs.copyFileSync(a, b)
  }
}

if (!fs.existsSync(path.join(src, 'index.html'))) {
  console.error('missing web build:', src)
  process.exit(1)
}
rm(dest)
copyDir(src, dest)
console.log('copied', src, '->', dest)
