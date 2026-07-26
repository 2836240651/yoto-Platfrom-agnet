// Deploy platform-mcp gateway to the production host (not the developer laptop).
// Prefer repo .env (gitignore). Required keys:
//   DEPLOY_PASS              SSH password (alias: $env:P)
//   DOUYIN_WORKER_TOKEN      shared with meat worker
//   COMMANDER_ACCESS_TOKEN   optional but recommended (Temu)
// Optional: DEPLOY_HOST, DEPLOY_USER, SOCIAL_UPLOAD_TOKEN
//
//   python scripts/_fill_douyin_worker_env.py   // generate worker token + defaults
//   scripts\deploy-platform-mcp.bat
//   scripts\start-douyin-meat-worker.bat
//
// After deploy, clients use:
//   https://www.yoto.work/platform-mcp/mcp
// Docs: docs/wip/douyin-meat-machine-mcp.md

const fs = require("fs");
const path = require("path");
const { Client } = require("ssh2");

const ROOT = path.resolve(__dirname, "..");

/** Load KEY=VAL from repo .env into process.env if not already set. */
function loadDotEnv(filePath) {
  if (!fs.existsSync(filePath)) return;
  const text = fs.readFileSync(filePath, "utf8");
  for (const line of text.split(/\r?\n/)) {
    const s = line.trim();
    if (!s || s.startsWith("#") || !s.includes("=")) continue;
    const i = s.indexOf("=");
    const key = s.slice(0, i).trim();
    let val = s.slice(i + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    if (process.env[key] === undefined || process.env[key] === "") {
      process.env[key] = val;
    }
  }
}

loadDotEnv(path.join(ROOT, ".env"));

const HOST = process.env.DEPLOY_HOST || "124.223.27.98";
const USER = process.env.DEPLOY_USER || "root";
const PASS = process.env.P || process.env.DEPLOY_PASS || "";
const REMOTE_DIR = "/data/platform-mcp";
const NGINX_PROXY =
  "/opt/1panel/www/sites/www.yoto.work/proxy/platform-mcp.conf";

const FILES = [
  ["mcp/servers/platform_mcp_gateway.py", "platform_mcp_gateway.py"],
  ["mcp/servers/commander_temu_client.py", "commander_temu_client.py"],
  ["mcp/servers/social_automedia_client.py", "social_automedia_client.py"],
  ["mcp/servers/douyin_job_queue.py", "douyin_job_queue.py"],
  ["mcp/deploy/Dockerfile", "Dockerfile"],
  ["mcp/deploy/platform-mcp.nginx.conf", "platform-mcp.nginx.conf"],
];

function exec(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let out = "";
      stream.on("data", (d) => (out += d.toString()));
      stream.stderr.on("data", (d) => (out += d.toString()));
      stream.on("close", (code) => resolve({ code, out }));
    });
  });
}

function upload(conn, local, remote) {
  return new Promise((resolve, reject) => {
    conn.sftp((err, sftp) => {
      if (err) return reject(err);
      sftp.fastPut(local, remote, (e) => (e ? reject(e) : resolve()));
    });
  });
}

function writeRemote(conn, remote, body) {
  return new Promise((resolve, reject) => {
    conn.sftp((err, sftp) => {
      if (err) return reject(err);
      const ws = sftp.createWriteStream(remote);
      ws.end(body);
      ws.on("close", resolve);
      ws.on("error", reject);
    });
  });
}

async function main() {
  if (!PASS) {
    console.error(
      "Set DEPLOY_PASS (or $env:P) in repo .env — SSH password for " +
        `${USER}@${HOST}`
    );
    process.exit(1);
  }
  const token = (process.env.COMMANDER_ACCESS_TOKEN || "").trim();
  const commanderAgentId = (process.env.COMMANDER_DEFAULT_AGENT_ID || "肉机").trim();
  const douyinWorkerToken = (
    process.env.DOUYIN_WORKER_TOKEN ||
    process.env.DOUYIN_WORKER_TOKEN_SET ||
    ""
  ).trim();
  const douyinWorkerTokenExpiresAt = (
    process.env.DOUYIN_WORKER_TOKEN_EXPIRES_AT || ""
  ).trim();
  if (!douyinWorkerToken) {
    console.error(
      "Set DOUYIN_WORKER_TOKEN in repo .env (shared with meat worker)"
    );
    process.exit(1);
  }
  const conn = new Client();
  await new Promise((resolve, reject) => {
    conn
      .on("ready", resolve)
      .on("error", reject)
      .connect({
        host: HOST,
        port: 22,
        username: USER,
        password: PASS,
        readyTimeout: 60000,
      });
  });

  console.log("mkdir", REMOTE_DIR);
  await exec(
    conn,
    `mkdir -p ${REMOTE_DIR}/uploads ${REMOTE_DIR}/build ${REMOTE_DIR}/douyin-jobs`
  );

  for (const [rel, name] of FILES) {
    const local = path.join(ROOT, rel);
    if (!fs.existsSync(local)) {
      throw new Error(`missing ${local}`);
    }
    const remote = `${REMOTE_DIR}/build/${name}`;
    console.log("upload", rel, "->", remote);
    await upload(conn, local, remote);
  }

  const socialToken = (process.env.SOCIAL_UPLOAD_TOKEN || "").trim();
  const compose = `services:
  platform-mcp:
    build:
      context: .
      dockerfile: Dockerfile
    image: platform-mcp:local
    container_name: platform-mcp
    restart: unless-stopped
    env_file:
      - .env
    environment:
      FASTMCP_HOST: "0.0.0.0"
      FASTMCP_PORT: "18765"
      FASTMCP_TRANSPORT: streamable-http
      DOUYIN_JOB_DIR: /data/douyin-jobs
    ports:
      - "127.0.0.1:18765:18765"
    volumes:
      - ${REMOTE_DIR}/uploads:/data/uploads:ro
      - ${REMOTE_DIR}/douyin-jobs:/data/douyin-jobs
    networks:
      - agent-platform

networks:
  agent-platform:
    external: true
    name: agent-platform-net
`;
  const envBody = [
    "COMMANDER_API_BASE=https://www.yoto.work/api/v1",
    `COMMANDER_ACCESS_TOKEN=${token}`,
    `COMMANDER_DEFAULT_AGENT_ID=${commanderAgentId}`,
    "COMMANDER_DEFAULT_PLATFORM=temu",
    `DOUYIN_WORKER_TOKEN=${douyinWorkerToken}`,
    `DOUYIN_WORKER_TOKEN_EXPIRES_AT=${douyinWorkerTokenExpiresAt}`,
    "DOUYIN_JOB_DIR=/data/douyin-jobs",
    "DOUYIN_JOB_TIMEOUT_S=360",
    "SOCIAL_UPLOAD_API_BASE=https://automedia.yoto.work",
    `SOCIAL_UPLOAD_TOKEN=${socialToken}`,
    "",
  ].join("\n");

  await writeRemote(conn, `${REMOTE_DIR}/build/docker-compose.yml`, compose);
  await writeRemote(conn, `${REMOTE_DIR}/build/.env`, envBody);
  await exec(conn, `chmod 600 ${REMOTE_DIR}/build/.env`);

  // Install nginx fragment + reload openresty
  await exec(
    conn,
    `cp ${REMOTE_DIR}/build/platform-mcp.nginx.conf ${NGINX_PROXY} && docker exec 1Panel-openresty-UN3Y nginx -t && docker exec 1Panel-openresty-UN3Y nginx -s reload`
  );

  console.log("docker compose up...");
  // Replace the existing named container platform-mcp (same gateway; do not spawn a second MCP).
  const build = await exec(
    conn,
    [
      `cd ${REMOTE_DIR}/build`,
      "docker compose down --remove-orphans 2>/dev/null || true",
      "docker rm -f platform-mcp 2>/dev/null || true",
      "docker compose build",
      "docker compose up -d",
    ].join(" && ")
  );
  console.log(build.out);
  if (build.code !== 0) {
    conn.end();
    process.exit(build.code || 1);
  }

  const check = await exec(
    conn,
    [
      "docker ps --filter name=platform-mcp --format '{{.Names}} {{.Status}} {{.Ports}}'",
      "sleep 2",
      "curl -s -o /dev/null -w 'local:%{http_code}\\n' -X POST http://127.0.0.1:18765/mcp -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"deploy\",\"version\":\"0\"}}}' || true",
      "curl -s -o /dev/null -w 'proxy:%{http_code}\\n' -X POST https://www.yoto.work/platform-mcp/mcp -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"deploy\",\"version\":\"0\"}}}' || true",
    ].join("; ")
  );
  console.log(check.out);
  console.log("TOKEN_SET", Boolean(token));
  console.log("CLIENT_URL https://www.yoto.work/platform-mcp/mcp");
  conn.end();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
