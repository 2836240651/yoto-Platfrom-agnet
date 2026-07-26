# Agent Platform API — same host as platform-mcp; shares UPLOAD_ROOT.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY skills ./skills
COPY knowledge ./knowledge
COPY apps/api ./apps/api

# China PyPI mirror — docker.io/pypi.org pulls are too slow on this host.
RUN pip install --no-cache-dir \
      -i https://pypi.tuna.tsinghua.edu.cn/simple \
      --trusted-host pypi.tuna.tsinghua.edu.cn \
      -e . \
    && pip install --no-cache-dir \
      -i https://pypi.tuna.tsinghua.edu.cn/simple \
      --trusted-host pypi.tuna.tsinghua.edu.cn \
      -r apps/api/requirements.txt

ENV PYTHONUNBUFFERED=1
ENV AGENT_ENV=prod
ENV MCP_RUNTIME_ENABLED=true
ENV MCP_ALLOW_STUB_FALLBACK=false
ENV MCP_CONFIG_PATH=/app/config/mcp.docker.json
ENV UPLOAD_ROOT=/data/platform-mcp/uploads

EXPOSE 8000
WORKDIR /app/apps/api
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
