# 重复总控入口归档

2026-10-29，按用户要求，项目根目录成为唯一总控入口，当前主 Agent 继续承担 `operations_director`。商品、流量领域及按需专项的职责沿用现有路由。

原 `agents/operations_director/AGENTS.md` 逐字保存为本目录的 `ENTRY.md`；原目录已移出活跃入口，不留软链接。`ENTRY.md` 中的指令和相对链接仅用于追溯，不执行、不按本目录解析，也不需要在日常任务中读取。

当前使用根 [AGENTS.md](../../AGENTS.md)、[角色注册表](../../catalog/agent-registry.json)及[任务路由](../../catalog/task-routing.json)。总控的能力技能仍保留，按具体任务加载。

[迁移记录](../../manifests/director-entry-consolidation-20261029.json)保存原路径、归档路径和 SHA-256；本次修改前文件保存在 `outputs/director-entry-consolidation-20261029/before/`。10月28日的30份旧角色归档及其清单保持原样。
