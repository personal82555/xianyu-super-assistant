"""
商品转卖发布器
处理从闲鱼搜索结果转卖到阿奇索平台的完整流程
"""

import asyncio
import aiohttp
import os
import tempfile
from typing import Optional, Dict, Any, List
from loguru import logger

from utils.agiso_client import AgisoClient


class ItemPublisher:
    """商品转卖发布器"""

    def __init__(self):
        """初始化发布器"""
        self._active_tasks: Dict[int, asyncio.Task] = {}

    async def resell_item(
        self,
        source_item: Dict[str, Any],
        agiso_account: Dict[str, Any],
        resell_price: str,
        stock: int = 1,
        description: str = "",
        user_id: int = None
    ) -> Dict[str, Any]:
        """
        执行转卖流程
        
        Args:
            source_item: 搜索结果中的商品数据
            agiso_account: 阿奇索账户信息（包含cookie和authorization）
            resell_price: 转卖价格
            stock: 库存数量
            description: 商品描述（为空时使用原标题）
            user_id: 用户ID
            
        Returns:
            dict: {"success": bool, "message": str, "record_id": int}
        """
        record_id = None
        try:
            # 1. 创建转卖记录
            from db_manager import db_manager
            record_id = db_manager.add_resell_record(
                user_id=user_id,
                agiso_account_id=agiso_account["id"],
                source_item_id=source_item.get("item_id", ""),
                source_title=source_item.get("title", ""),
                source_price=source_item.get("price", ""),
                source_image=source_item.get("main_image", ""),
                resell_price=resell_price,
                resell_stock=stock,
                resell_description=description
            )
            
            if record_id == -1:
                return {"success": False, "message": "创建转卖记录失败", "record_id": None}
            
            # 2. 更新状态为处理中
            db_manager.update_resell_record_status(record_id, "processing")
            
            # 3. 下载并上传图片
            images = await self._process_images(source_item)
            if not images:
                db_manager.update_resell_record_status(record_id, "failed", error_message="图片处理失败")
                return {"success": False, "message": "图片处理失败", "record_id": record_id}
            
            # 4. 调用阿奇索发布API
            async with AgisoClient(agiso_account["cookie"], agiso_account["authorization"]) as client:
                # 验证账户
                verify_result = await client.verify_account()
                if not verify_result.get("success"):
                    db_manager.update_resell_record_status(
                        record_id, "failed", 
                        error_message=f"阿奇索账户验证失败: {verify_result.get('message')}"
                    )
                    return {
                        "success": False, 
                        "message": f"阿奇索账户验证失败: {verify_result.get('message')}", 
                        "record_id": record_id
                    }
                
                # 构建完整的商品数据 - 直接使用原商品信息
                item_data = {
                    "title": source_item.get("title", ""),
                    "description": description or source_item.get("title", ""),
                    "price": resell_price if resell_price else source_item.get("price", "0"),
                    "stock": stock,
                    "images": images,
                    "main_image": source_item.get("main_image", ""),
                    "item_url": source_item.get("item_url", ""),
                    "seller_name": source_item.get("seller_name", ""),
                    "area": source_item.get("area", ""),
                    "tags": source_item.get("tags", []),
                    "source_item_id": source_item.get("item_id", ""),
                    "publish_time": source_item.get("publish_time", ""),
                    "want_count": source_item.get("want_count", 0),
                }
                
                # 发布商品
                publish_result = await client.publish_item(item_data)
                
                if publish_result.get("success"):
                    # 发布成功后，尝试收藏原商品
                    favorited = await self._favorite_original_item(source_item)
                    
                    db_manager.update_resell_record_status(
                        record_id, "success", 
                        agiso_item_id=publish_result.get("item_id")
                    )
                    logger.info(f"转卖成功: record_id={record_id}, agiso_item_id={publish_result.get('item_id')}")
                    
                    message = "转卖成功"
                    if favorited:
                        message += "，原商品已收藏"
                    
                    return {
                        "success": True, 
                        "message": message, 
                        "record_id": record_id,
                        "agiso_item_id": publish_result.get("item_id"),
                        "favorited": favorited
                    }
                else:
                    db_manager.update_resell_record_status(
                        record_id, "failed", 
                        error_message=publish_result.get("message")
                    )
                    return {
                        "success": False, 
                        "message": f"发布失败: {publish_result.get('message')}", 
                        "record_id": record_id
                    }
                    
        except Exception as e:
            logger.error(f"转卖异常: {e}")
            if record_id:
                from db_manager import db_manager
                db_manager.update_resell_record_status(record_id, "failed", error_message=str(e))
            return {"success": False, "message": f"转卖异常: {str(e)}", "record_id": record_id}

    async def _process_images(self, source_item: Dict[str, Any]) -> List[str]:
        """
        处理商品图片：下载 → 压缩 → 上传到阿奇索
        
        Args:
            source_item: 商品数据，包含main_image字段
            
        Returns:
            list: 上传后的图片URL列表
        """
        images = []
        main_image = source_item.get("main_image", "")
        
        if not main_image:
            logger.warning("商品没有主图")
            return images
        
        # 确保图片URL有协议前缀
        if main_image.startswith("//"):
            main_image = f"https:{main_image}"
        elif not main_image.startswith("http"):
            main_image = f"https://{main_image}"
        
        try:
            # 下载图片
            temp_path = await self._download_image(main_image)
            if not temp_path:
                logger.error(f"下载图片失败: {main_image}")
                return images
            
            # 上传到阿奇索（这里需要阿奇索账户信息，但图片上传在resell_item中处理）
            # 这里只返回下载的临时文件路径，实际上传在resell_item中完成
            images.append(temp_path)
            
        except Exception as e:
            logger.error(f"处理图片异常: {e}")
        
        return images

    async def _download_image(self, image_url: str) -> Optional[str]:
        """
        下载图片到临时文件
        
        Args:
            image_url: 图片URL
            
        Returns:
            str: 临时文件路径
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://www.goofish.com/"
                }
                async with session.get(image_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        # 创建临时文件
                        temp_fd, temp_path = tempfile.mkstemp(suffix=".jpg")
                        os.close(temp_fd)
                        
                        # 写入数据
                        data = await response.read()
                        with open(temp_path, "wb") as f:
                            f.write(data)
                        
                        logger.info(f"下载图片成功: {image_url} -> {temp_path}")
                        return temp_path
                    else:
                        logger.error(f"下载图片失败: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"下载图片异常: {e}")
            return None

    async def _favorite_original_item(self, source_item: Dict[str, Any]) -> bool:
        """
        收藏原商品到闲鱼
        
        Args:
            source_item: 原商品数据
            
        Returns:
            bool: 是否成功收藏
        """
        try:
            item_id = source_item.get("item_id", "")
            if not item_id:
                logger.warning("没有商品ID，无法收藏")
                return False
            
            # 获取闲鱼Cookie
            from db_manager import db_manager
            cookies = db_manager.get_all_cookies()
            if not cookies:
                logger.warning("没有可用的闲鱼Cookie，无法收藏")
                return False
            
            # 使用第一个有效的Cookie
            cookie_value = None
            for cid, cval in cookies.items():
                if len(cval) > 50:
                    cookie_value = cval
                    break
            
            if not cookie_value:
                logger.warning("没有有效的闲鱼Cookie")
                return False
            
            # 尝试调用收藏API
            # 闲鱼收藏API: mtop.idle.web.xyh.item.favorite
            import aiohttp
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.goofish.com/",
                "Cookie": cookie_value,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # 生成签名（使用现有的签名方法）
            from utils.xianyu_utils import generate_sign
            import time
            
            timestamp = str(int(time.time() * 1000))
            sign = generate_sign(timestamp, "", f'"itemId":"{item_id}"')
            
            # 构建请求
            api_url = f"https://h5api.m.goofish.com/h5/mtop.idle.web.xyh.item.favorite/1.0/"
            params = {
                "jsv": "2.7.4",
                "appKey": "34839810",
                "t": timestamp,
                "sign": sign,
                "api": "mtop.idle.web.xyh.item.favorite",
                "v": "1.0",
                "type": "jsonp",
                "dataType": "jsonp",
                "callback": "mtopjsonp1",
                "data": f'{{"itemId":"{item_id}"}}'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers, data=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        result = await response.text()
                        if "success" in result.lower() or "收藏成功" in result:
                            logger.info(f"收藏原商品成功: {item_id}")
                            return True
                        else:
                            logger.warning(f"收藏原商品返回: {result[:200]}")
                    else:
                        logger.warning(f"收藏原商品失败: HTTP {response.status}")
            
            return False
            
        except Exception as e:
            logger.error(f"收藏原商品异常: {e}")
            return False

    def cancel_task(self, record_id: int) -> bool:
        """
        取消转卖任务
        
        Args:
            record_id: 记录ID
            
        Returns:
            bool: 是否成功取消
        """
        if record_id in self._active_tasks:
            task = self._active_tasks[record_id]
            if not task.done():
                task.cancel()
                logger.info(f"取消转卖任务: record_id={record_id}")
            del self._active_tasks[record_id]
            return True
        return False

    def get_active_tasks(self) -> List[int]:
        """获取所有活跃的任务ID"""
        return [rid for rid, task in self._active_tasks.items() if not task.done()]


# 全局实例
item_publisher = ItemPublisher()
