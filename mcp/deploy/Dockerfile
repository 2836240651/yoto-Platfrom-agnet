# Platform MCP gateway — runs on deploy host (not developer laptop).
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "mcp>=1.2.0" "httpx>=0.27.0" "uvicorn>=0.30.0" "starlette>=0.37.0"

COPY commander_temu_client.py social_automedia_client.py douyin_job_queue.py platform_mcp_gateway.py ./

ENV FASTMCP_HOST=0.0.0.0
ENV FASTMCP_PORT=18765
ENV FASTMCP_TRANSPORT=streamable-http
ENV COMMANDER_API_BASE=https://www.yoto.work/api/v1
ENV COMMANDER_DEFAULT_AGENT_ID=肉机
ENV COMMANDER_DEFAULT_PLATFORM=temu
ENV DOUYIN_JOB_DIR=/data/douyin-jobs

EXPOSE 18765

CMD ["python", "platform_mcp_gateway.py"]
