# 🚀 闲鱼超级助手 (Xianyu Super Assistant)

> **闲鱼卖家必备的全自动化管理神器** — 多账号、智能回复、自动发货、一键托管

---

## 📸 演示地址

https://xianyu.88531.cn/admin 

## 📸 界面预览

<img width="3364" height="348" alt="image" src="https://github.com/user-attachments/assets/72f640b0-6cd7-4531-ac26-d7c777031719" />
<img width="601" height="1399" alt="PixPin_2026-07-06_09-35-22" src="https://github.com/user-attachments/assets/64dbf44a-5d80-4223-a794-0f271e7ee5cc" />
<img width="3418" height="1289" alt="image" src="https://github.com/user-attachments/assets/fd723e4a-cfed-4e1d-a04a-a32ad31577f9" />
<img width="3394" height="1777" alt="image" src="https://github.com/user-attachments/assets/539c0fbc-39eb-4909-949f-23ee34b61293" />
<img width="3388" height="712" alt="image" src="https://github.com/user-attachments/assets/8bb87fa8-1535-4ae1-a7ce-f3c1c37c68a7" />
<img width="3220" height="1574" alt="image" src="https://github.com/user-attachments/assets/72932083-dc35-471d-90e8-085e8a874ede" />






---

## ✨ 核心功能

### 🤖 智能自动回复
- **AI 智能回复** — 接入 OpenAI 兼容 API（通义千问等），自动识别买家意图（询价/售后/咨询），生成个性化回复
- **关键词精准匹配** — 自定义关键词库，命中即回复，支持图片消息
- **HTTP 回调接口** — 对接外部业务系统，灵活扩展

### 📦 订单全自动处理
- **自动发货** — 数字商品秒级自动发送，支持每账号独立冷却
- **自动确认发货** — 调用闲鱼官方 API，智能防重复
- **自动免邮** — 拼团订单自动包邮处理
- **订单详情自动抓取** — Playwright 无头浏览器，自动获取订单信息

### 👥 多账号管理
- 无限账号同时在线，互不干扰
- 每账号独立关键词、AI 配置、自动开关
- 独立冷却/暂停策略，智能避免与人工冲突

### 🌐 Web 管理面板
- 美观的 SPA 单页应用，Bootstrap 5 响应式设计
- 账号管理、商品管理、订单管理、关键词管理
- 实时日志流查看
- 数据备份/恢复
- 多用户权限系统（管理员/普通用户）

### 📢 多渠道通知
- **QQ**、**钉钉**、**企业微信**、**Telegram**
- **Email** 邮件通知、**Webhook** 通用回调
- 新消息、令牌刷新失败、发货失败实时告警

### 🔐 安全稳定
- WebSocket 心跳保活（15秒间隔）+ 自动重连
- 令牌 20 小时自动刷新
- 请求签名加密（JS 引擎 + 协议缓冲区）
- Docker 一键部署，自带健康检查
- Nginx 反向代理支持（SSL/WebSocket）

---

## 🚀 快速开始

### Docker 部署（推荐）

```bash
git clone https://github.com/personal82555/xianyu-super-assistant.git
cd xianyu-super-assistant

# 启动服务
bash docker-deploy.sh start

# 查看状态
bash docker-deploy.sh status

# 查看日志
bash docker-deploy.sh logs
```

然后访问 **http://localhost:8080** 进入管理面板。

### 手动部署

```bash
pip install -r requirements.txt
playwright install chromium
python Start.py
```

### 配置说明

编辑 `global_config.yml` 或通过环境变量配置：

```yaml
AUTO_REPLY:
  enabled: true           # 开启自动回复
  default_message: '...'  # 默认回复语

TOKEN_REFRESH_INTERVAL: 72000  # 令牌刷新间隔（秒）
HEARTBEAT_INTERVAL: 15         # WebSocket 心跳间隔（秒）
```

---

## 📖 使用指南

1. **添加账号** — 在管理面板通过二维码或手动输入 Cookie 添加闲鱼账号
2. **配置关键词** — 为每个账号设置专属关键词回复库
3. **开启 AI 回复** — 配置 OpenAI API Key，开启智能回复
4. **设置自动发货** — 添加数字商品，系统自动完成发货
5. **开启自动确认/包邮** — 一键托管订单处理

---

## 🏗️ 技术架构

- **后端**: Python 3.11+ / FastAPI / Uvicorn / asyncio
- **前端**: Bootstrap 5 / Vanilla JS / SPA
- **存储**: SQLite (线程安全)
- **AI**: OpenAI SDK / 通义千问 API
- **自动化**: Playwright (Chromium 无头浏览器)
- **通信**: WebSocket / HTTP / Protobuf
- **部署**: Docker / docker-compose / Nginx

---

## 📄 开源协议

MIT License

---

> ⚡ **闲鱼超级助手** — 让闲鱼卖货更轻松，多账号托管从未如此简单！
