# 项目架构

## 整体结构

```
xianyu-super-dev/
├── Start.py                   # 入口：启动 FastAPI + 账号任务
├── XianyuAutoAsync.py         # 🔴 核心协程（巨无霸，200KB）
├── db_manager.py              # 🔴 数据库操作（巨无霸，200KB）
├── reply_server.py            # FastAPI Web 管理面板后端
├── ai_reply_engine.py         # AI 智能回复引擎
├── cookie_manager.py          # 多账号 Cookie 管理
├── config.py                  # Config 单例，管理 global_config.yml
├── global_config.yml          # YAML 配置文件
├── file_log_collector.py      # 日志文件收集器
├── secure_*.py                # 闲鱼 API 签名加密模块
├── utils/
│   ├── image_uploader.py      # 图片上传
│   ├── image_utils.py         # 图片处理
│   ├── item_search.py         # 商品搜索
│   ├── message_utils.py       # 消息工具
│   ├── order_detail_fetcher.py# 订单详情抓取（Playwright）
│   ├── qr_login.py            # 二维码登录
│   ├── ws_utils.py            # WebSocket 工具
│   └── xianyu_utils.py        # 闲鱼通用工具函数
├── static/                    # Web 面板前端（SPA）
├── nginx/                     # Nginx 反向代理配置
├── Dockerfile                 # 多阶段构建
├── docker-compose.yml         # Docker 编排
└── docker-deploy.sh           # 部署脚本
```

## 启动流程

```
Start.py  main()
  │
  ├─ setup_file_logging()         ← 初始化日志
  ├─ CookieManager 初始化账号任务  ← 多账号加载
  │     └─ 每个账号创建异步任务
  │           ├─ WebSocket 连接
  │           ├─ 消息监听循环
  │           ├─ 心跳保活 (15s)
  │           └─ Token 自动刷新 (20h)
  ├─ 后台线程启动 FastAPI
  │     └─ reply_server.py: /api/xxx 管理接口
  └─ 主协程保持运行
```

## 任务架构

**每个账号是一个独立异步任务**，由 `asyncio.create_task()` 启动：

```
账号任务 (每个账号一个)
├── WebSocket 连接 → wss://wss-goofish.dingtalk.com/
├── 接收消息 → 意图分类 → AI回复/关键词回复
├── 心跳保活 (15秒间隔)
├── Token 自动刷新 (20小时)
└── 多通道通知（QQ/钉钉/企微/Telegram/Email）
```

## 通知架构

支持多渠道并行通知：

```
事件触发
  ├─ QQ 通知（go-cqhttp）
  ├─ 钉钉机器人
  ├─ 企业微信
  ├─ Telegram Bot
  ├─ Email
  └─ Webhook
```

## 数据库

- **引擎**: SQLite（`xianyu_data.db`）
- **操作入口**: `db_manager.py` 提供的接口
- **勿直接写 SQL**: 尽量通过 db_manager 的方法操作

## 配置分层

```
.env               → 敏感信息（API Key、密钥、密码）— 不提交 git
global_config.yml  → 功能配置（API 端点、超时、开关）— 提交 git
```

## 安全机制

- 请求签名：`secure_*.py` 使用 JS 引擎（PyExecJS）+ 协议缓冲区加密
- Token 管理：20 小时有效期，自动刷新
- WebSocket：wss 协议 + 心跳保活 + 自动重连
- 多用户权限系统：管理员 / 普通用户
