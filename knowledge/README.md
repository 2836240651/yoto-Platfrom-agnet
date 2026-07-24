# Knowledge Base

向量知识库与入库脚本目录。

```
knowledge/
├── collections/          # 原始文档（按业务域）
│   ├── ecommerce-ops/
│   └── douyin-analytics/
├── index/                # 向量索引（gitignore）
│   └── chroma/
└── ingest/               # 入库脚本（TODO）
```

## 记忆类型映射

| 类型 | 存储 | 目录 |
|------|------|------|
| 语义记忆 | Vector DB | `collections/` + `index/` |
| 情景记忆 | SQL | `src/agent/memory/episodic.py` |
| 程序记忆 | Skill 文件 | `skills/` |
| 实体记忆 | SQL/Redis | `src/agent/memory/entity.py` |
