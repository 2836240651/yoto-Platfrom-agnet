// Hot-patch agent-platform-api on yoto without full pip rebuild.
// Syncs collect→analyze→report Skill path + tools status dual-hand probes.
//
//   node scripts/deploy-agent-api-hotpatch.js
//
// Requires DEPLOY_PASS (or $env:P) and optional DOUYIN_WORKER_TOKEN in repo .env.

const fs = require("fs");
const path = require("path");
const { Client } = require("ssh2");

const ROOT = path.resolve(__dirname, "..");

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
const REMOTE_APP = "/data/agent-platform/app";
const REMOTE_COMPOSE = "/data/agent-platform";
const CONTAINER = "agent-platform-api";

const REL_FILES = [
  "src/agent/constants.py",
  "src/agent/llm.py",
  "src/agent/config/settings.py",
  "src/agent/knowledge/__init__.py",
  "src/agent/knowledge/fishing_gear.py",
  "src/agent/tools/douyin_analyze.py",
  "src/agent/tools/step_handlers.py",
  "src/agent/tools/stub_dispatch.py",
  "src/agent/tools/arg_builders.py",
  "src/agent/nodes/act.py",
  "src/agent/nodes/generate.py",
  "src/agent/nodes/init_task.py",
  "src/agent/nodes/route.py",
  "src/agent/nodes/validate.py",
  "src/agent/state.py",
  "config/tool_registry.json",
  "config/mcp.json",
  "config/mcp.docker.json",
  "mcp/deploy/api.Dockerfile",
  "apps/api/app/services/tools_status.py",
  "apps/api/app/services/langgraph_runner.py",
  "apps/api/app/services/report_adapter.py",
  "apps/api/app/routers/tasks.py",
  "apps/api/app/routers/tools.py",
  "apps/api/app/main.py",
  "apps/api/app/schemas/tasks.py",
  "apps/api/app/store/task_store.py",
  "skills/douyin-keyword-research/SKILL.md",
  "skills/douyin-keyword-research/schema/input.json",
  "skills/douyin-keyword-research/schema/output.json",
  "knowledge/collections/fishing-gear/catalog.json",
  "knowledge/collections/fishing-gear/README.md",
];

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
  return new Promise((resolve) => {
    const parts = remoteDir.split("/").filter(Boolean);
    let cur = "";
    const next = (i) => {
      if (i >= parts.length) return resolve();
      cur += "/" + parts[i];
      sftpClient.mkdir(cur, () => next(i + 1));
    };
    next(0);
  });
}

function uploadFile(sftpClient, local, remote) {
  return new Promise((resolve, reject) => {
    sftpClient.fastPut(local, remote, (e) => (e ? reject(e) : resolve()));
  });
}

async function main() {
  if (!PASS) {
    console.error("Set DEPLOY_PASS (or $env:P) in repo .env");
    process.exit(1);
  }
const douyinToken = (process.env.DOUYIN_WORKER_TOKEN || "").trim();
const commanderAccessToken = (process.env.COMMANDER_ACCESS_TOKEN || "").trim();
const commanderApiBase = (
  process.env.COMMANDER_API_BASE || "https://www.yoto.work/api/v1"
).trim();
const commanderDefaultAgentId = (
  process.env.COMMANDER_DEFAULT_AGENT_ID || "肉机"
).trim();
const commanderDefaultPlatform = (
  process.env.COMMANDER_DEFAULT_PLATFORM || "temu"
).trim();
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
        readyTimeout: 120000,
      });
  });

  const s = await sftp(conn);
  console.log("ensure remote dirs...");
  await exec(conn, `mkdir -p ${REMOTE_APP}`);

  const present = [];
  for (const rel of REL_FILES) {
    const local = path.join(ROOT, rel);
    if (!fs.existsSync(local)) {
      console.warn("skip missing", rel);
      continue;
    }
    const remote = `${REMOTE_APP}/${rel}`.replace(/\\/g, "/");
    await mkdirp(s, remote.slice(0, remote.lastIndexOf("/")));
    console.log("upload", rel);
    await uploadFile(s, local, remote);
    present.push(rel);
  }

  if (douyinToken) {
    console.log("merge DOUYIN_WORKER_* into compose .env...");
    const pyBody = `
from pathlib import Path
import re
p = Path(${JSON.stringify(REMOTE_COMPOSE + "/.env")})
text = p.read_text(encoding="utf-8") if p.exists() else ""
vals = {
    "DOUYIN_WORKER_TOKEN": ${JSON.stringify(douyinToken)},
    "DOUYIN_WORKER_URL": "https://www.yoto.work/platform-mcp",
    "COMMANDER_API_BASE": ${JSON.stringify(commanderApiBase)},
    "COMMANDER_ACCESS_TOKEN": ${JSON.stringify(commanderAccessToken)},
    "COMMANDER_DEFAULT_AGENT_ID": ${JSON.stringify(commanderDefaultAgentId)},
    "COMMANDER_DEFAULT_PLATFORM": ${JSON.stringify(commanderDefaultPlatform)},
    "AGENT_ENV": "prod",
    "MCP_ALLOW_STUB_FALLBACK": "false",
    "LLM_MODEL": "gpt-5.6-terra",
    "LLM_HEAVY_MODEL": "gpt-5.6-terra",
}
for k, v in vals.items():
    if re.search(rf"^{k}=.*$", text, flags=re.M):
        text = re.sub(rf"^{k}=.*$", f"{k}={v}", text, flags=re.M)
    else:
        text = text.rstrip() + "\\n" + f"{k}={v}" + "\\n"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(text if text.endswith("\\n") else text + "\\n", encoding="utf-8")
print("ok", p)
`.trim();
    await new Promise((resolve, reject) => {
      const ws = s.createWriteStream("/tmp/merge_douyin_env.py");
      ws.end(pyBody + "\n");
      ws.on("close", resolve);
      ws.on("error", reject);
    });
    const merge = await exec(conn, "python3 /tmp/merge_douyin_env.py");
    console.log(merge.out.trim());
  }

  console.log("docker cp into", CONTAINER, "...");
  const ps = await exec(
    conn,
    `docker ps --filter name=${CONTAINER} --format '{{.Names}} {{.Status}}'`
  );
  console.log(ps.out.trim());
  if (!ps.out.includes(CONTAINER)) {
    console.error("container not running");
    conn.end();
    process.exit(1);
  }

  // One shell script remotely to avoid channel spam
  const scriptLines = ["set -e"];
  for (const rel of present) {
    const remote = `${REMOTE_APP}/${rel}`.replace(/\\/g, "/");
    const inContainer = `/app/${rel}`.replace(/\\/g, "/");
    const inDir = inContainer.slice(0, inContainer.lastIndexOf("/"));
    scriptLines.push(`docker exec ${CONTAINER} mkdir -p ${inDir}`);
    scriptLines.push(`docker cp ${remote} ${CONTAINER}:${inContainer}`);
  }
  scriptLines.push(
    `docker compose -f ${REMOTE_COMPOSE}/docker-compose.yml build agent-api`
  );
  scriptLines.push(
    `docker compose -f ${REMOTE_COMPOSE}/docker-compose.yml up -d --no-deps --force-recreate agent-api`
  );
  scriptLines.push("sleep 5");
  scriptLines.push("curl -s http://127.0.0.1:18000/api/health || true");
  scriptLines.push("echo");
  scriptLines.push(
    `docker exec ${CONTAINER} python -c "from agent.constants import SKILL_PLANS; print([x.get('name') for x in SKILL_PLANS['douyin-keyword-research']])"`
  );

  const remoteScript = "/tmp/agent-api-hotpatch.sh";
  await new Promise((resolve, reject) => {
    const ws = s.createWriteStream(remoteScript);
    ws.end(scriptLines.join("\n") + "\n");
    ws.on("close", resolve);
    ws.on("error", reject);
  });
  await exec(conn, `chmod +x ${remoteScript}`);
  const run = await exec(conn, `bash ${remoteScript}`);
  console.log(run.out);
  if (run.code !== 0) {
    conn.end();
    process.exit(run.code || 1);
  }

  if (!run.out.includes("analyze") || run.out.includes("expand")) {
    console.error("WARN: skill plan may not be collect/analyze/report");
  } else {
    console.log("skill_plan_ok collect analyze report");
  }

  console.log("API https://www.yoto.work/agent-platform/api/docs");
  console.log("tools https://www.yoto.work/agent-platform/api/tools/status");
  conn.end();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
