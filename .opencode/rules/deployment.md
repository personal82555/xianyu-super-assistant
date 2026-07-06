# 部署与运维

## Docker 开发

```bash
# 构建镜像
docker build -t xianyu-super:dev .

# 启动
docker compose up -d

# 查看日志
docker compose logs -f

# 仅构建不缓存
docker build --no-cache -t xianyu-super:dev .
```

## Docker Compose

- `docker-compose.yml` → 生产部署用
- `docker-compose-cn.yml` → 国内镜像源版本
- 不要手动修改线上 docker-compose，改代码后通过自动化流程部署
- 暴露端口：`8080:8080`（Web 管理面板）

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `API_HOST` | API 绑定地址 | `0.0.0.0` |
| `API_PORT` | API 端口 | `8080` |
| `OPENAI_API_KEY` | AI 回复的 API Key | 来自 `.env` |

## Nginx

- 配置在 `nginx/` 目录
- 支持 SSL 和 WebSocket 反向代理
- 开发环境通常不需要 nginx，直接访问 `http://localhost:8080`

## 日志

- `realtime.log` — 运行时日志（不提交 git）
- `start.log` — 启动日志（不提交 git）
- `logs/` — 按日期轮转的日志目录（不提交 git）
- 使用 `docker compose logs -f` 查看实时日志
- 日志轮转：每天一次，保留 7 天

## 启动方式

```bash
# 方式1：Docker（推荐）
bash docker-deploy.sh start

# 方式2：直接 Python
python Start.py
```

## 健康检查

- Docker 容器有健康检查配置
- WebSocket 心跳：每 15 秒
- Token 自动刷新：每 20 小时
- 网络断开自动重连
