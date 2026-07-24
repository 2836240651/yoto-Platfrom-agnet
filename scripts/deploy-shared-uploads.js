// Deploy platform-mcp + agent-api on the same host with shared UPLOAD_ROOT.
// Usage (PowerShell):
//   $env:P = '<ssh password>'
//   $env:NODE_PATH = 'D:\dev\workspace\scripts\_ssh-probe\node_modules'
//   node scripts/deploy-shared-uploads.js
//
// Preserves existing COMMANDER_ACCESS_TOKEN from /data/platform-mcp/build/.env when present.

const fs = require("fs");
const path = require("path");
const { Client } = require("ssh2");

const HOST = process.env.DEPLOY_HOST || "124.223.27.98";
const USER = process.env.DEPLOY_USER || "root";
const PASS = process.env.P || process.env.DEPLOY_PASS || "";
const ROOT = path.resolve(__dirname, "..");

const REMOTE_MCP = "/data/platform-mcp";
const REMOTE_APP = "/data/agent-platform/app";
const REMOTE_COMPOSE = "/data/agent-platform";
const UPLOADS = "/data/platform-mcp/uploads";
const NGINX_MCP = "/opt/1panel/www/sites/www.yoto.work/proxy/platform-mcp.conf";
const NGINX_API = "/opt/1panel/www/sites/www.yoto.work/proxy/agent-platform.conf";

const MCP_FILES = [
  ["mcp/servers/platform_mcp_gateway.py", `${REMOTE_MCP}/build/platform_mcp_gateway.py`],
  ["mcp/servers/commander_temu_client.py", `${REMOTE_MCP}/build/commander_temu_client.py`],
  ["mcp/deploy/Dockerfile", `${REMOTE_MCP}/build/Dockerfile`],
  ["mcp/deploy/platform-mcp.nginx.conf", `${REMOTE_MCP}/build/platform-mcp.nginx.conf`],
  ["mcp/deploy/agent-platform.nginx.conf", `${REMOTE_MCP}/build/agent-platform.nginx.conf`],
];

const APP_DIRS = ["src", "config", "skills", "apps/api", "mcp/deploy"];
const APP_FILES = ["pyproject.toml", "README.md"];

function exec(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, { maxBuffer: 20 * 1024 * 1024 }, (err, stream) => {
      if (err) return reject(err);
      let out = "";
      stream.on("data", (d) => (out += d.toString()));
      stream.stderr.on("data", (d) => (out += d.toString()));
      stream.on("close", (code) => resolve({ code, out }));
    });
  });
}

function sftp(conn) {
  return new Promise((resolve, reject) => {
    conn.sftp((err, s) => (err ? reject(err) : resolve(s)));
  });
}

function mkdirp(sftpClient, remoteDir) {
  return new Promise((resolve, reject) => {
    const parts = remoteDir.split("/").filter(Boolean);
    let cur = "";
    const next = (i) => {
      if (i >= parts.length) return resolve();
      cur += "/" + parts[i];
      sftpClient.mkdir(cur, (err) => {
        // ignore exists
        next(i + 1);
      });
    };
    next(0);
  });
}

function uploadFile(sftpClient, local, remote) {
  return new Promise((resolve, reject) => {
    sftpClient.fastPut(local, remote, (e) => (e ? reject(e) : resolve()));
  });
}

async function uploadTree(sftpClient, localDir, remoteDir) {
  await mkdirp(sftpClient, remoteDir);
  const entries = fs.readdirSync(localDir, { withFileTypes: true });
  for (const ent of entries) {
    if (ent.name === "__pycache__" || ent.name === ".pytest_cache" || ent.name === "node_modules") {
      continue;
    }
    const lp = path.join(localDir, ent.name);
    const rp = `${remoteDir}/${ent.name}`.replace(/\\/g, "/");
    if (ent.isDirectory()) {
      await uploadTree(sftpClient, lp, rp);
    } else {
      await mkdirp(sftpClient, path.posix.dirname(rp));
      await uploadFile(sftpClient, lp, rp);
    }
  }
}

function writeRemote(sftpClient, remote, body) {
  return new Promise((resolve, reject) => {
    const ws = sftpClient.createWriteStream(remote);
    ws.end(body);
    ws.on("close", resolve);
    ws.on("error", reject);
  });
}

async function main() {
  if (!PASS) {
    console.error("Set P or DEPLOY_PASS");
    process.exit(1);
  }
  const conn = new Client();
  await new Promise((resolve, reject) => {
    conn
      .on("ready", resolve)
      .on("error", reject)
      .connect({ host: HOST, port: 22, username: USER, password: PASS, readyTimeout: 120000 });
  });

  const s = await sftp(conn);
  console.log("mkdirs...");
  await exec(
    conn,
    `mkdir -p ${REMOTE_MCP}/build ${UPLOADS} ${REMOTE_APP} ${REMOTE_COMPOSE}`
  );

  for (const [rel, remote] of MCP_FILES) {
    console.log("mcp", rel);
    await uploadFile(s, path.join(ROOT, rel), remote);
  }

  for (const rel of APP_FILES) {
    console.log("app file", rel);
    await uploadFile(s, path.join(ROOT, rel), `${REMOTE_APP}/${rel}`);
  }
  for (const rel of APP_DIRS) {
    console.log("app dir", rel);
    await uploadTree(s, path.join(ROOT, rel), `${REMOTE_APP}/${rel}`);
  }

  // Preserve token from previous mcp .env if present
  const oldEnv = await exec(conn, `cat ${REMOTE_MCP}/build/.env 2>/dev/null || true`);
  let token = (process.env.COMMANDER_ACCESS_TOKEN || "").trim();
  if (!token) {
    const m = oldEnv.out.match(/^COMMANDER_ACCESS_TOKEN=(.*)$/m);
    if (m) token = (m[1] || "").trim();
  }
  const openai = (process.env.OPENAI_API_KEY || "").trim();
  const openaiBase =
    (process.env.OPENAI_API_BASE || "").trim() || "https://api.hyhacct.com/v1";
  const llmModel = (process.env.LLM_MODEL || "").trim() || "gpt-5.6-luna";
  const heavyKey = (process.env.LLM_HEAVY_API_KEY || "").trim() || openai;
  const heavyModel =
    (process.env.LLM_HEAVY_MODEL || "").trim() || llmModel || "gpt-5.6-luna";
  const lightKey = (process.env.LLM_LIGHT_API_KEY || "").trim();
  const lightModel =
    (process.env.LLM_LIGHT_MODEL || "").trim() || "agnes-2.0-flash";

  const envBody = [
    "COMMANDER_API_BASE=https://www.yoto.work/api/v1",
    `COMMANDER_ACCESS_TOKEN=${token}`,
    "COMMANDER_DEFAULT_AGENT_ID=肉机",
    "COMMANDER_DEFAULT_PLATFORM=temu",
    "UPLOAD_ROOT=/data/platform-mcp/uploads",
    "AGENT_ENV=prod",
    "MCP_RUNTIME_ENABLED=true",
    "MCP_ALLOW_STUB_FALLBACK=false",
    "MCP_CONFIG_PATH=/app/config/mcp.docker.json",
    openai ? `OPENAI_API_KEY=${openai}` : "OPENAI_API_KEY=",
    `OPENAI_API_BASE=${openaiBase}`,
    `LLM_MODEL=${llmModel}`,
    heavyKey ? `LLM_HEAVY_API_KEY=${heavyKey}` : "LLM_HEAVY_API_KEY=",
    `LLM_HEAVY_MODEL=${heavyModel}`,
    lightKey ? `LLM_LIGHT_API_KEY=${lightKey}` : "LLM_LIGHT_API_KEY=",
    `LLM_LIGHT_MODEL=${lightModel}`,
    "",
  ].join("\n");

  const compose = `services:
  platform-mcp:
    build:
      context: ${REMOTE_MCP}/build
      dockerfile: Dockerfile
    image: platform-mcp:local
    container_name: platform-mcp
    restart: unless-stopped
    env_file:
      - ${REMOTE_COMPOSE}/.env
    environment:
      FASTMCP_HOST: "0.0.0.0"
      FASTMCP_PORT: "18765"
      FASTMCP_TRANSPORT: streamable-http
    ports:
      - "127.0.0.1:18765:18765"
    volumes:
      - ${UPLOADS}:${UPLOADS}:ro
    networks:
      - platform

  agent-api:
    build:
      context: ${REMOTE_APP}
      dockerfile: mcp/deploy/api.Dockerfile
    image: agent-platform-api:local
    container_name: agent-platform-api
    restart: unless-stopped
    env_file:
      - ${REMOTE_COMPOSE}/.env
    environment:
      UPLOAD_ROOT: ${UPLOADS}
      MCP_CONFIG_PATH: /app/config/mcp.docker.json
      AGENT_ENV: prod
      MCP_RUNTIME_ENABLED: "true"
      MCP_ALLOW_STUB_FALLBACK: "false"
    ports:
      - "127.0.0.1:18000:8000"
    volumes:
      - ${UPLOADS}:${UPLOADS}
    depends_on:
      - platform-mcp
    networks:
      - platform

networks:
  platform:
    name: agent-platform-net
`;

  await writeRemote(s, `${REMOTE_COMPOSE}/docker-compose.yml`, compose);
  await writeRemote(s, `${REMOTE_COMPOSE}/.env`, envBody);
  await writeRemote(s, `${REMOTE_MCP}/build/.env`, envBody);
  await exec(conn, `chmod 600 ${REMOTE_COMPOSE}/.env ${REMOTE_MCP}/build/.env`);

  console.log("nginx...");
  const ngx = await exec(
    conn,
    `cp ${REMOTE_MCP}/build/platform-mcp.nginx.conf ${NGINX_MCP}; cp ${REMOTE_MCP}/build/agent-platform.nginx.conf ${NGINX_API}; docker exec 1Panel-openresty-UN3Y nginx -t && docker exec 1Panel-openresty-UN3Y nginx -s reload`
  );
  console.log(ngx.out);

  console.log("docker compose up (may take several minutes)...");
  const up = await exec(
    conn,
    `cd ${REMOTE_COMPOSE} && docker compose down --remove-orphans 2>/dev/null; docker compose build && docker compose up -d`
  );
  console.log(up.out);
  if (up.code !== 0) {
    conn.end();
    process.exit(up.code || 1);
  }

  const check = await exec(
    conn,
    [
      "docker ps --filter name=platform-mcp --format '{{.Names}} {{.Status}} {{.Ports}}'",
      "docker ps --filter name=agent-platform-api --format '{{.Names}} {{.Status}} {{.Ports}}'",
      "sleep 3",
      // create marker file via API upload using a tiny xlsx zip header is hard; write host file and check container sees it
      `echo shared-ok > ${UPLOADS}/_probe.txt`,
      `docker exec platform-mcp test -f ${UPLOADS}/_probe.txt && echo MCP_SEES_UPLOADS=yes || echo MCP_SEES_UPLOADS=no`,
      `docker exec agent-platform-api test -f ${UPLOADS}/_probe.txt && echo API_SEES_UPLOADS=yes || echo API_SEES_UPLOADS=no`,
      "curl -s -o /dev/null -w 'api_health:%{http_code}\\n' http://127.0.0.1:18000/api/health || true",
      "curl -s -o /dev/null -w 'api_proxy:%{http_code}\\n' https://www.yoto.work/agent-platform/api/health || true",
    ].join("; ")
  );
  console.log(check.out);
  console.log("TOKEN_SET", Boolean(token));
  console.log("UPLOAD_ROOT", UPLOADS);
  console.log("API https://www.yoto.work/agent-platform/api/docs");
  conn.end();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
