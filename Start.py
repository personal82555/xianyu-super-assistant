"""项目启动入口：

1. 创建 CookieManager，按配置文件 / 环境变量初始化账号任务
2. 在后台线程启动 FastAPI (reply_server) 提供管理与自动回复接口
3. 主协程保持运行
"""

import os
import asyncio
import threading
import uvicorn
from urllib.parse import urlparse
from pathlib import Path
from loguru import logger

from config import AUTO_REPLY, COOKIES_LIST
import cookie_manager as cm
from db_manager import db_manager
from file_log_collector import setup_file_logging


def _start_api_server():
    """后台线程启动 FastAPI 服务"""
    api_conf = AUTO_REPLY.get('api', {})

    # 优先使用环境变量配置
    host = os.getenv('API_HOST', '0.0.0.0')  # 默认绑定所有接口
    port = int(os.getenv('API_PORT', '8080'))  # 默认端口8080

    # 如果配置文件中有特定配置，则使用配置文件
    if 'host' in api_conf:
        host = api_conf['host']
    if 'port' in api_conf:
        port = api_conf['port']

    # 兼容旧的URL配置方式
    if 'url' in api_conf and 'host' not in api_conf and 'port' not in api_conf:
        url = api_conf.get('url', 'http://0.0.0.0:8080/xianyu/reply')
        parsed = urlparse(url)
        if parsed.hostname and parsed.hostname != 'localhost':
            host = parsed.hostname
        port = parsed.port or 8080

    logger.info(f"启动Web服务器: http://{host}:{port}")
    uvicorn.run("reply_server:app", host=host, port=port, log_level="info")


def load_keywords_file(path: str):
    """从文件读取关键字 -> [(keyword, reply)]"""
    kw_list = []
    p = Path(path)
    if not p.exists():
        return kw_list
    with p.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '\t' in line:
                k, r = line.split('\t', 1)
            elif ' ' in line:
                k, r = line.split(' ', 1)
            elif ':' in line:
                k, r = line.split(':', 1)
            else:
                continue
            kw_list.append((k.strip(), r.strip()))
    return kw_list


async def main():
    print("开始启动主程序...")

    # 初始化文件日志收集器
    print("初始化文件日志收集器...")
    setup_file_logging()
    logger.info("文件日志收集器已启动，开始收集实时日志")

    loop = asyncio.get_running_loop()

    # 创建 CookieManager 并在全局暴露
    print("创建 CookieManager...")
    cm.manager = cm.CookieManager(loop)
    manager = cm.manager
    print("CookieManager 创建完成")

    # 1) 从数据库加载的 Cookie 已经在 CookieManager 初始化时完成
    # 为每个启用的 Cookie 启动任务
    for cid, val in manager.cookies.items():
        # 检查账号是否启用
        if not manager.get_cookie_status(cid):
            logger.info(f"跳过禁用的 Cookie: {cid}")
            continue

        try:
            # 直接启动任务，不重新保存到数据库
            from db_manager import db_manager
            logger.info(f"正在获取Cookie详细信息: {cid}")
            cookie_info = db_manager.get_cookie_details(cid)
            user_id = cookie_info.get('user_id') if cookie_info else None
            logger.info(f"Cookie详细信息获取成功: {cid}, user_id: {user_id}")

            logger.info(f"正在创建异步任务: {cid}")
            task = loop.create_task(manager._run_xianyu(cid, val, user_id))
            manager.tasks[cid] = task
            logger.info(f"启动数据库中的 Cookie 任务: {cid} (用户ID: {user_id})")
            logger.info(f"任务已添加到管理器，当前任务数: {len(manager.tasks)}")
        except Exception as e:
            logger.error(f"启动 Cookie 任务失败: {cid}, {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
    
    # 2) 如果配置文件中有新的 Cookie，也加载它们
    for entry in COOKIES_LIST:
        cid = entry.get('id')
        val = entry.get('value')
        if not cid or not val or cid in manager.cookies:
            continue
        
        kw_file = entry.get('keywords_file')
        kw_list = load_keywords_file(kw_file) if kw_file else None
        manager.add_cookie(cid, val, kw_list)
        logger.info(f"从配置文件加载 Cookie: {cid}")

    # 3) 若老环境变量仍提供单账号 Cookie，则作为 default 账号
    env_cookie = os.getenv('COOKIES_STR')
    if env_cookie and 'default' not in manager.list_cookies():
        manager.add_cookie('default', env_cookie)
        logger.info("从环境变量加载 default Cookie")

    # 启动 API 服务线程
    print("启动 API 服务线程...")
    threading.Thread(target=_start_api_server, daemon=True).start()
    print("API 服务线程已启动")

    # 阻塞保持运行
    print("主程序启动完成，保持运行...")
    await asyncio.Event().wait()


if __name__ == '__main__':
    asyncio.run(main()) 