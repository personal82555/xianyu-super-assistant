# 更新日志

## v2.2.0 (2026-07-09)

### 🐛 Bug Fixes

- **修复自动发货商品归属检查失败** — 当商品不在 `item_info` 表时，先尝试通过 API 获取并保存，而不是直接跳过自动发货
- **修复 API 超时错误** — `get_item_info` 添加 15 秒超时，解决 "Timeout context manager should be used inside a task" 问题
- **修复重新发货使用错误账号** — 重新发货时从 `item_info` 表查找商品真正的卖家账号，而不是使用订单的 `cookie_id`
- **修复重新发货消息发送失败** — 使用 `xianyu_instance.ws` 发送消息，之前传了 `None` 导致发送失败
- **修复重新发货 API 认证失败** — 添加 `Content-Type: application/json` header
- **修复订单管理 API 未返回新字段** — `/admin/orders` 接口补充查询 `delivery_status` 和 `buyer_name` 字段
- **修复买家账号也执行自动发货** — 添加卖家身份校验，只有卖家账号才触发自动发货
- **修复重新发货商品标题获取失败** — 从全库 `item_info` 表搜索商品标题，不局限于订单的 `cookie_id`

### ✨ New Features

- **订单发货状态跟踪** — `orders` 表新增 `delivery_status` 字段，支持 `pending`/`delivered`/`failed` 三种状态
- **买家昵称显示** — `orders` 表新增 `buyer_name` 字段，自动保存买家昵称，订单列表显示友好名称
- **重新发货功能** — 所有订单支持"再发一次货"按钮（列表+详情弹窗），可手动重新触发自动发货
- **新订单自动保存商品标题** — 检测到新订单时，从消息的 `itemTitle` 字段自动保存到 `item_info` 表，确保发货规则匹配
- **订单详情页展示发货状态** — 订单详情弹窗显示发货状态 badge 和重新发货按钮

### 🔧 Improvements

- **优化商品归属检查逻辑** — 自动发货和免拼发货均支持 API fallback，不再因 `item_info` 缺失而跳过
- **CookieManager 缓存 XianyuLive 实例** — 新增 `xianyu_instances` 字典，支持通过 API 获取在线实例
- **前端 JS 文件版本号防缓存** — `app.js` 添加 `?v=2` 参数

### 📝 Database Migration

- `orders` 表新增 `delivery_status TEXT DEFAULT 'pending'`
- `orders` 表新增 `buyer_name TEXT DEFAULT ''`

---

## v2.1.0 (2026-07-06)

- 🎉 初始版本发布
- 多账号管理、智能自动回复、自动发货
- Web 管理面板、数据备份/恢复
