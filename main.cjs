/**
 * TUODIAO Workspace shell.
 *
 * Online https://www.yoto.work/agent-platform/ currently proxies ONLY the API
 * (JSON 404 for SPA). Members need a working UI, so this shell:
 *   1) serves the bundled apps/web build on 127.0.0.1
 *   2) proxies /api → https://www.yoto.work/agent-platform/api
 *
 * MeatWorker stays a separate EXE on the idle host.
 */
const { app, BrowserWindow, shell, Menu, nativeImage } = require('electron')
const http = require('http')
const https = require('https')
const path = require('path')
const fs = require('fs')
const { URL } = require('url')

const APP_TITLE = 'TUODIAO'
const API_UPSTREAM = (
  process.env.YOTO_API_BASE || 'https://www.yoto.work/agent-platform'
).replace(/\/$/, '')

/** Optional: force remote SPA URL (only when that URL actually serves HTML). */
const REMOTE_SPA = (process.env.YOTO_WORKSPACE_URL || '').trim()

/** @type {BrowserWindow | null} */
let mainWindow = null
/** @type {http.Server | null} */
let localServer = null
let localOrigin = ''

function resolveIcon() {
  const candidates = [
    path.join(__dirname, 'build', 'icon.ico'),
    path.join(__dirname, 'build', 'icon.png'),
    path.join(process.resourcesPath || '', 'build', 'icon.ico'),
  ]
  for (const p of candidates) {
    if (fs.existsSync(p)) {
      const img = nativeImage.createFromPath(p)
      if (!img.isEmpty()) return img
    }
  }
  return undefined
}

function webDistDir() {
  const candidates = [
    path.join(__dirname, 'web-dist'),
    path.join(process.resourcesPath || '', 'web-dist'),
  ]
  for (const p of candidates) {
    if (fs.existsSync(path.join(p, 'index.html'))) return p
  }
  return null
}

function contentType(filePath) {
  const ext = path.extname(filePath).toLowerCase()
  return (
    {
      '.html': 'text/html; charset=utf-8',
      '.js': 'text/javascript; charset=utf-8',
      '.css': 'text/css; charset=utf-8',
      '.json': 'application/json',
      '.svg': 'image/svg+xml',
      '.png': 'image/png',
      '.ico': 'image/x-icon',
      '.woff': 'font/woff',
      '.woff2': 'font/woff2',
      '.map': 'application/json',
    }[ext] || 'application/octet-stream'
  )
}

function proxyApi(req, res) {
  const upstream = new URL(API_UPSTREAM + req.url)
  const lib = upstream.protocol === 'https:' ? https : http
  const headers = { ...req.headers, host: upstream.host }
  delete headers['origin']
  delete headers['referer']

  const preq = lib.request(
    {
      protocol: upstream.protocol,
      hostname: upstream.hostname,
      port: upstream.port || (upstream.protocol === 'https:' ? 443 : 80),
      path: upstream.pathname + upstream.search,
      method: req.method,
      headers,
    },
    (pres) => {
      res.writeHead(pres.statusCode || 502, pres.headers)
      pres.pipe(res)
    },
  )
  preq.on('error', (err) => {
    res.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' })
    res.end(JSON.stringify({ detail: `API 代理失败: ${err.message}` }))
  })
  req.pipe(preq)
}

function serveStatic(req, res, root) {
  try {
    const u = new URL(req.url || '/', 'http://127.0.0.1')
    let rel = decodeURIComponent(u.pathname)
    if (rel === '/' || rel === '') rel = '/index.html'
    const filePath = path.normalize(path.join(root, rel))
    if (!filePath.startsWith(path.normalize(root))) {
      res.writeHead(403)
      res.end('Forbidden')
      return
    }
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      // SPA fallback
      const index = path.join(root, 'index.html')
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' })
      fs.createReadStream(index).pipe(res)
      return
    }
    res.writeHead(200, { 'Content-Type': contentType(filePath) })
    fs.createReadStream(filePath).pipe(res)
  } catch (err) {
    res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' })
    res.end(String(err))
  }
}

function startLocalServer(root) {
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      if ((req.url || '').startsWith('/api')) {
        proxyApi(req, res)
        return
      }
      serveStatic(req, res, root)
    })
    server.once('error', reject)
    server.listen(0, '127.0.0.1', () => {
      const addr = server.address()
      if (!addr || typeof addr === 'string') {
        reject(new Error('bad listen address'))
        return
      }
      localServer = server
      localOrigin = `http://127.0.0.1:${addr.port}`
      resolve(localOrigin)
    })
  })
}

function splashHtml(message) {
  return `<!doctype html><html><head><meta charset="utf-8"><title>${APP_TITLE}</title>
<style>
  html,body{margin:0;height:100%;background:#0a0a0a;color:#f5f5f5;
    font-family:"Segoe UI",system-ui,sans-serif;display:flex;align-items:center;justify-content:center}
  .wrap{text-align:center;max-width:36rem;padding:1.5rem}
  .mark{font-size:12px;opacity:.5;margin-bottom:16px;letter-spacing:.45em}
  h1{font-weight:700;font-size:28px;margin:0 0 14px;letter-spacing:.32em}
  p{opacity:.7;font-size:14px;line-height:1.6;margin:0;letter-spacing:.04em}
</style></head><body>
  <div class="wrap">
    <div class="mark">WORKSPACE</div>
    <h1>${APP_TITLE}</h1>
    <p>${message || '正在启动…'}</p>
  </div>
</body></html>`
}

function showSplash(message) {
  if (!mainWindow) return
  return mainWindow.loadURL(
    `data:text/html;charset=utf-8,${encodeURIComponent(splashHtml(message))}`,
  )
}

async function createWindow() {
  const icon = resolveIcon()
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 960,
    minHeight: 640,
    title: APP_TITLE,
    icon,
    show: false,
    backgroundColor: '#0a0a0a',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  })

  mainWindow.setMenuBarVisibility(false)
  mainWindow.once('ready-to-show', () => {
    if (mainWindow) mainWindow.show()
  })
  mainWindow.on('page-title-updated', (e) => {
    e.preventDefault()
    if (mainWindow) mainWindow.setTitle(APP_TITLE)
  })

  mainWindow.webContents.on('did-fail-load', (_e, code, desc, url, isMain) => {
    if (!isMain || code === -3) return // -3 = aborted
    console.error('did-fail-load', code, desc, url)
    showSplash(`页面加载失败<br/>${desc} (${code})<br/><br/>${url}`)
  })

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const target = new URL(url)
      if (localOrigin && target.origin === new URL(localOrigin).origin) {
        return { action: 'allow' }
      }
      if (target.hostname === 'www.yoto.work' || target.hostname === 'yoto.work') {
        return { action: 'allow' }
      }
    } catch {
      /* fall through */
    }
    shell.openExternal(url)
    return { action: 'deny' }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  await showSplash('正在启动 Workspace…')

  try {
    let target = REMOTE_SPA
    if (!target) {
      const root = webDistDir()
      if (!root) {
        throw new Error(
          '未找到内置前端 web-dist。请运行 scripts\\build-workspace-desktop.bat 重新打包。',
        )
      }
      target = await startLocalServer(root)
    }
    await mainWindow.loadURL(target)
  } catch (err) {
    console.error('boot failed', err)
    await showSplash(`启动失败<br/><br/>${String(err)}`)
  }
}

function buildMenu() {
  const template = [
    {
      label: APP_TITLE,
      submenu: [
        {
          label: '重新加载',
          accelerator: 'CmdOrCtrl+R',
          click: () => {
            if (mainWindow) mainWindow.reload()
          },
        },
        {
          label: '在浏览器打开线上 API 文档',
          click: () => shell.openExternal(`${API_UPSTREAM}/api/docs`),
        },
        { type: 'separator' },
        {
          label: '关于 TUODIAO',
          click: () => {
            const { dialog } = require('electron')
            dialog.showMessageBox({
              type: 'info',
              title: APP_TITLE,
              message: 'TUODIAO Workspace',
              detail:
                `跨境智能体客户端\nAPI：${API_UPSTREAM}\n` +
                (localOrigin ? `本地壳：${localOrigin}\n` : '') +
                '\n采集请在闲置主机运行 MeatWorker.exe。',
              icon: resolveIcon(),
            })
          },
        },
        { type: 'separator' },
        { role: 'quit', label: '退出' },
      ],
    },
    {
      label: '查看',
      submenu: [
        { role: 'togglefullscreen', label: '全屏' },
        { role: 'resetZoom', label: '实际大小' },
        { role: 'zoomIn', label: '放大' },
        { role: 'zoomOut', label: '缩小' },
        { type: 'separator' },
        { role: 'toggleDevTools', label: '开发者工具' },
      ],
    },
  ]
  Menu.setApplicationMenu(Menu.buildFromTemplate(template))
}

app.whenReady().then(async () => {
  if (process.platform === 'win32') {
    app.setAppUserModelId('work.tuodiao.workspace')
  }
  buildMenu()
  await createWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (localServer) {
    try {
      localServer.close()
    } catch {
      /* ignore */
    }
    localServer = null
  }
  if (process.platform !== 'darwin') app.quit()
})
