# 闲鱼超级助手 - AI 作业规则

## 项目概要

闲鱼多账号自动化管理工具。Python asyncio + FastAPI + WebSocket 架构。核心文件都在项目根目录，utils/ 放工具模块。

## 关键文件速查

| 文件 | 作用 | 注意 |
|------|------|------|
| `XianyuAutoAsync.py` (205KB) | 主力协程代码，单文件巨无霸 | 不要在这文件里新增功能，优先拆到独立文件 |
| `db_manager.py` (215KB) | 数据库操作，也是单文件巨无霸 | 同上原则 |
| `reply_server.py` (171KB) | FastAPI Web 管理后端 | |
| `ai_reply_engine.py` | AI 智能回复引擎，调用 OpenAI API | |
| `cookie_manager.py` | 多账号 Cookie 管理 | |
| `config.py` | 全局配置单例 | 读/写 `global_config.yml` |
| `global_config.yml` | YAML 配置文件 | |
| `Start.py` | 项目入口 | |

## 开发约定

### 代码风格
- 不要修改 `XianyuAutoAsync.py` 和 `db_manager.py` 已有逻辑除非修复 bug——新功能写独立文件
- 函数参数和返回值加类型注解
- 异步函数用 `async def`，阻塞操作用 `asyncio.to_thread()` 或 loop.run_in_executor
- 日志用 `loguru` 的 `logger`，不要用 `print`
- 字符串用双引号

### 配置
- 项目配置在 `global_config.yml`，通过 `Config` 单例类读写
- 敏感信息（API Key、密钥）放 `.env` 文件，不上传到 git
- 新配置项加到 `global_config.yml` 有默认值

### 数据库
- SQLite，文件是 `xianyu_data.db`（已被 .gitignore 排除）
- 通过 `db_manager.py` 提供的接口操作
- 不要在业务代码里直接写 SQL，除非性能有要求

### Git
- 分支名：`feat/xxx`、`fix/xxx`、`chore/xxx`、`refactor/xxx`
- Commit: `type(scope): 中文描述`（如 `feat(auto-reply): 支持图片消息回复`）
- 不要提交 `.env`、`*.db`、`logs/`、`realtime.log`、`start.log`
- GitHub 仓库: `personal82555/xianyu-super-assistant`

### Docker
- 开发环境不要动 `docker-compose.yml`，改本地测试
- `Dockerfile` 多阶段构建，安装依赖后拷贝源码
- 部署前检查 nginx 配置和 WebSocket 路径

### AI 回复
- `ai_reply_engine.py` 调用 OpenAI 兼容 API，不同账号有独立 client
- 意图分类：price / tech / refund / default
- 回复长度限制：每句 ≤10 字，总字数 ≤40 字
