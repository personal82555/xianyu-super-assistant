# 闲鱼 API 端点

## API 基础

- 域名: `h5api.m.goofish.com`
- 认证: Cookie + 请求签名
- 签名: 使用 `secure_*.py` 中的 JS 引擎加密

## 主要端点 (global_config.yml API_ENDPOINTS)

| 端点键名 | URL | 用途 |
|----------|-----|------|
| `login_check` | `passport.goofish.com/newlogin/hasLogin.do` | 登录状态检查 |
| `message_headinfo` | `h5api.m.goofish.com/h5/mtop.idle.trade.pc.message.headinfo/1.0/` | 消息头部信息 |
| `token` | `h5api.m.goofish.com/h5/mtop.taobao.idlemessage.pc.login.token/1.0/` | Token 获取 |

## WebSocket

- URL: `wss://wss-goofish.dingtalk.com/`
- 心跳间隔: 15 秒
- Header 需要带上 `Cookie` 和自定义 `Origin`

## 请求签名

- 位置: `secure_confirm_decrypted.py`, `secure_freeshipping_decrypted.py`
- 使用 PyExecJS 执行 JS 加密
- 请求头参见 `global_config.yml` 的 `DEFAULT_HEADERS`

## 商品详情外部 API

- URL: `https://selfapi.zhinianboke.com/api/getItemDetail`
- 并发限制: 3
- 超时: 30 秒
