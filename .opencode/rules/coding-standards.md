# 编码规范

## Python 通用

- Python >= 3.10，使用 asyncio 异步编程
- 类型注解：**函数参数和返回值必须标注类型**，包括 `async def`
  - `def get_user(user_id: int) -> Optional[dict]:`
  - `async def send_message(msg: str, timeout: int = 10) -> bool:`
- 字符串用**双引号**（`, 不要单引号）
- 类名：`PascalCase`（`CookieManager`, `AIReplyEngine`）
- 函数/变量：`snake_case`（`auto_reply`, `max_retry`）
- 常量：`UPPER_SNAKE_CASE`（`TOKEN_REFRESH_INTERVAL`, `HEARTBEAT_INTERVAL`）

## 日志（loguru）

- **禁止使用 `print()`**，全部用 `from loguru import logger`
- 日志分级合理：`INFO` 记录流程、`WARNING` 记录异常但不影响运行、`ERROR` 记录失败、`DEBUG` 详细调试

```python
logger.info(f"开始处理账号 {account_name} 的消息")
logger.warning(f"Token 刷新失败，{e}")
logger.error(f"WebSocket 断开: {e}")
```

## 异步编程

- I/O 操作（HTTP、WebSocket、数据库查询）必须 `async/await`
- CPU 密集或阻塞操作用 `asyncio.to_thread()` 或 `loop.run_in_executor()`
- 所有异步函数用 `async def`，调用时 `await`
- WebSocket 心跳用 `asyncio.create_task()` 后台运行，不要用 `threading`

## 配置

- 新增配置项时：先在 `global_config.yml` 加默认值，再通过 `Config.get()` 读取
- 敏感信息（API Key、密钥、密码）：只从 `.env` 读取，不要硬编码
- `Config` 是单例，直接 `from config import Config; cfg = Config()` 获取

## 错误处理

- 网络请求必须加超时（`timeout` 参数）和重试（`max_retry` + `retry_interval`）
- 捕获具体异常类型，不要裸 `except:`
- 外部 API 调用失败时：记录 `ERROR` 日志 + 重试，不要崩溃

```python
# ✅
try:
    result = await send_request(url, timeout=10)
except aiohttp.ClientError as e:
    logger.error(f"请求失败: {e}")
    return None

# ❌
try:
    result = await send_request(url)
except:
    pass
```

## 单文件巨无霸原则

`XianyuAutoAsync.py` 和 `db_manager.py` 是历史遗留的大文件（各 200KB+）。

- **不在这两个文件加新功能**——新功能写独立文件
- 修复 bug 时，最小改动，加上注释说明
- 实在需要加逻辑时，优先拆成工具函数放到 `utils/` 目录
