# Handoff：采集源口径更正（蝉妈妈个人版）

- 日期：2026-07-23
- 状态：done

## 更正

- **旧误：** 写成蝉妈妈官方 OpenAPI /「原子 API」。  
- **正解：** 蝉妈妈**个人版会员**登录态（Cookie）+ **浏览器自动化**拉数；遵守个人版限制；Cookie 禁止入库。

## 已改文件

- `docs/spec-architecture-contract.md`（v1.1）  
- `docs/wip/spec-business-scenarios-llm-tool.md`  
- `docs/wip/p0-contract-gap-check.md`  
- `docs/spec-product.md`  
- `AGENTS.md`

## 下一步（用户将提供种子词）

在 open-reverselab 词卡/采集链路上本地全跑 → 产出 HTML（不写进 agent-platform 业务 Skill）。
