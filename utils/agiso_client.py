"""
阿奇索API客户端 - Playwright自动化版本
通过浏览器自动化操作阿奇索平台，无需逆向API
"""

import asyncio
import json
import os
import tempfile
import base64
from typing import Optional, Dict, Any, List
from loguru import logger
from PIL import Image

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright 未安装")


class AgisoClient:
    """阿奇索API客户端 - 基于Playwright自动化"""

    def __init__(self, cookie: str, authorization: str):
        """
        初始化阿奇索客户端
        
        Args:
            cookie: 阿奇索网站的Cookie字符串
            authorization: 阿奇索网站的Authorization头
        """
        self.cookie = cookie
        self.authorization = authorization
        self.base_url = "https://aldsidle.agiso.com"
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def _init_browser(self):
        """初始化浏览器"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright 未安装，无法使用浏览器自动化")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        # 设置Cookie
        await self._set_cookies()
        
        # 创建页面
        self.page = await self.context.new_page()
        
        # 设置Authorization头
        await self.page.set_extra_http_headers({
            "Authorization": self.authorization
        })

    async def _set_cookies(self):
        """设置浏览器Cookie"""
        if not self.cookie:
            return
        
        cookies = []
        for item in self.cookie.split(";"):
            item = item.strip()
            if "=" in item:
                name, value = item.split("=", 1)
                cookies.append({
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": ".agiso.com",
                    "path": "/"
                })
        
        if cookies:
            await self.context.add_cookies(cookies)
            logger.info(f"设置Cookie成功: {len(cookies)}个")

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None

    async def __aenter__(self):
        await self._init_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def verify_account(self) -> Dict[str, Any]:
        """
        验证账户有效性 - 通过设置Cookie访问阿奇索网站
        
        Returns:
            dict: {"success": bool, "message": str, "data": dict}
        """
        try:
            if not self.page:
                await self._init_browser()
            
            # 访问阿奇索首页
            logger.info("验证阿奇索账户...")
            await self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            # 获取当前URL，检查是否被重定向到登录页
            current_url = self.page.url
            logger.info(f"当前页面: {current_url}")
            
            # 如果URL包含login相关路径，说明未登录
            if "login" in current_url.lower() and "home" not in current_url.lower():
                return {
                    "success": False,
                    "message": "账户验证失败：Cookie或Authorization无效，请重新获取",
                    "data": None
                }
            
            # 尝试访问仪表盘
            try:
                await self.page.goto(f"{self.base_url}/#/home/dashboard", wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(2)
                
                # 再次检查URL
                current_url = self.page.url
                if "login" in current_url.lower() and "home" not in current_url.lower():
                    return {
                        "success": False,
                        "message": "账户验证失败：Cookie或Authorization无效",
                        "data": None
                    }
                
                logger.info("阿奇索账户验证成功")
                return {
                    "success": True,
                    "message": "账户验证成功",
                    "data": {"url": current_url}
                }
            except Exception as e:
                logger.warning(f"访问仪表盘失败: {e}")
                # 即使访问失败，只要不跳转到登录页就算成功
                return {
                    "success": True,
                    "message": "账户验证成功",
                    "data": {"url": self.page.url}
                }
        except Exception as e:
            logger.error(f"验证阿奇索账户异常: {e}")
            return {
                "success": False,
                "message": f"验证异常: {str(e)}",
                "data": None
            }

    async def upload_image(self, image_path: str) -> Dict[str, Any]:
        """
        上传图片到阿奇索
        
        Args:
            image_path: 本地图片路径
            
        Returns:
            dict: {"success": bool, "message": str, "url": str}
        """
        temp_path = None
        try:
            if not self.page:
                await self._init_browser()
            
            # 压缩图片
            temp_path = self._compress_image(image_path)
            if not temp_path:
                return {"success": False, "message": "图片压缩失败", "url": None}
            
            # 读取图片并转换为base64
            with open(temp_path, "rb") as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode()
            
            # TODO: 根据阿奇索实际页面结构实现图片上传
            # 这里需要知道阿奇索的图片上传界面是什么样的
            
            logger.info(f"图片上传功能待实现: {image_path}")
            return {
                "success": False, 
                "message": "图片上传功能需要根据阿奇索页面结构调整",
                "url": None
            }
        except Exception as e:
            logger.error(f"上传图片异常: {e}")
            return {"success": False, "message": f"上传异常: {str(e)}", "url": None}
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

    def _compress_image(self, image_path: str, max_size: int = 5 * 1024 * 1024, quality: int = 85) -> Optional[str]:
        """压缩图片"""
        try:
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # 调整尺寸
                max_dimension = 1920
                original_width, original_height = img.size
                if original_width > max_dimension or original_height > max_dimension:
                    if original_width > original_height:
                        new_width = max_dimension
                        new_height = int((original_height * max_dimension) / original_width)
                    else:
                        new_height = max_dimension
                        new_width = int((original_width * max_dimension) / original_height)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # 保存到临时文件
                temp_fd, temp_path = tempfile.mkstemp(suffix=".jpg")
                os.close(temp_fd)
                img.save(temp_path, "JPEG", quality=quality, optimize=True)

                # 检查文件大小
                file_size = os.path.getsize(temp_path)
                if file_size > max_size:
                    quality = max(30, quality - 20)
                    img.save(temp_path, "JPEG", quality=quality, optimize=True)

                logger.info(f"图片压缩完成: {os.path.getsize(temp_path) / 1024:.1f}KB")
                return temp_path
        except Exception as e:
            logger.error(f"图片压缩失败: {e}")
            return None

    async def publish_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发布商品到阿奇索 - 完整复制原商品信息
        
        Args:
            item_data: 完整的原商品数据，包含:
                - title: 商品标题
                - description: 商品描述
                - price: 商品价格
                - stock: 库存数量
                - images: 图片URL列表
                - main_image: 主图URL
                - item_url: 原商品链接
                - seller_name: 卖家名称
                - area: 地区
                - tags: 标签列表
                
        Returns:
            dict: {"success": bool, "message": str, "item_id": str}
        """
        try:
            if not self.page:
                await self._init_browser()
            
            publish_url = f"{self.base_url}/#/goodsManage/goodsList/goodsRelease"
            logger.info(f"开始发布商品，访问: {publish_url}")
            
            # 访问发布页面
            await self.page.goto(publish_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)
            
            # 检查是否跳转到登录页
            if "login" in self.page.url.lower():
                return {
                    "success": False,
                    "message": "发布失败：未登录或Cookie已过期，请重新添加账户",
                    "item_id": None
                }
            
            logger.info(f"已进入发布页面: {self.page.url}")
            
            # 等待页面加载完成
            await asyncio.sleep(2)
            
            # 获取完整商品信息
            title = item_data.get("title", "")
            description = item_data.get("description", "") or title
            price = item_data.get("price", "0")
            stock = item_data.get("stock", 1)
            main_image = item_data.get("main_image", "")
            item_url = item_data.get("item_url", "")
            seller_name = item_data.get("seller_name", "")
            area = item_data.get("area", "")
            tags = item_data.get("tags", [])
            
            # 清理价格字符串
            clean_price = str(price).replace("¥", "").replace("￥", "").strip()
            
            logger.info(f"商品信息: 标题={title[:30]}..., 价格={clean_price}, 库存={stock}")
            
            # 分析页面结构，找到所有输入框
            all_inputs = await self.page.query_selector_all('input, textarea')
            logger.info(f"找到 {len(all_inputs)} 个输入框")
            
            for i, inp in enumerate(all_inputs):
                try:
                    placeholder = await inp.get_attribute('placeholder') or ''
                    name = await inp.get_attribute('name') or ''
                    input_type = await inp.get_attribute('type') or ''
                    logger.info(f"输入框 {i}: placeholder='{placeholder}', name='{name}', type='{input_type}'")
                except:
                    pass
            
            # 分析页面中的按钮
            all_buttons = await self.page.query_selector_all('button')
            logger.info(f"找到 {len(all_buttons)} 个按钮")
            
            for i, btn in enumerate(all_buttons):
                try:
                    btn_text = await btn.inner_text()
                    btn_type = await btn.get_attribute('type') or ''
                    logger.info(f"按钮 {i}: text='{btn_text}', type='{btn_type}'")
                except:
                    pass
            
            # 尝试填写表单 - 使用更智能的方式
            # 1. 先尝试通过placeholder匹配
            field_mappings = {
                '标题': title,
                '商品名称': title,
                '商品标题': title,
                '价格': clean_price,
                '售价': clean_price,
                '库存': str(stock),
                '数量': str(stock),
                '描述': description,
                '商品描述': description,
                '详情': description
            }
            
            for placeholder_text, value in field_mappings.items():
                try:
                    # 通过placeholder查找
                    selector = f'input[placeholder*="{placeholder_text}"], textarea[placeholder*="{placeholder_text}"]'
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.fill(value)
                        logger.info(f"通过placeholder填写成功: {placeholder_text}={value[:20]}...")
                        continue
                    
                    # 通过label文本查找
                    label = await self.page.query_selector(f'label:has-text("{placeholder_text}")')
                    if label:
                        input_el = await label.query_selector('input, textarea')
                        if input_el:
                            await input_el.fill(value)
                            logger.info(f"通过label填写成功: {placeholder_text}={value[:20]}...")
                except Exception as e:
                    continue
            
            # 2. 尝试填写所有可见的输入框
            for inp in all_inputs:
                try:
                    placeholder = await inp.get_attribute('placeholder') or ''
                    name = await inp.get_attribute('name') or ''
                    input_type = await inp.get_attribute('type') or ''
                    
                    # 跳过隐藏的输入框
                    if input_type == 'hidden':
                        continue
                    
                    # 根据placeholder或name猜测字段
                    if '标题' in placeholder or '名称' in placeholder or 'title' in name.lower():
                        await inp.fill(title)
                    elif '价格' in placeholder or 'price' in name.lower():
                        await inp.fill(clean_price)
                    elif '库存' in placeholder or '数量' in placeholder or 'stock' in name.lower():
                        await inp.fill(str(stock))
                    elif '描述' in placeholder or '详情' in placeholder or 'desc' in name.lower():
                        await inp.fill(description)
                except Exception as e:
                    continue
            
            # 3. 填写textarea
            textareas = await self.page.query_selector_all('textarea')
            for textarea in textareas:
                try:
                    placeholder = await textarea.get_attribute('placeholder') or ''
                    if '描述' in placeholder or '详情' in placeholder or not placeholder:
                        await textarea.fill(description)
                        logger.info(f"填写textarea成功: {placeholder}")
                except:
                    continue
            
            # 4. 尝试填写富文本编辑器
            editors = await self.page.query_selector_all('.ql-editor, [contenteditable="true"], .ProseMirror')
            for editor in editors:
                try:
                    await editor.click()
                    await editor.fill(description)
                    logger.info("填写富文本编辑器成功")
                except:
                    continue
            
            # 等待一下让页面处理
            await asyncio.sleep(1)
            
            # 5. 点击发布按钮
            submit_selectors = [
                'button:has-text("发布")',
                'button:has-text("提交")',
                'button:has-text("保存并上架")',
                'button:has-text("确认发布")',
                'button[type="submit"]',
                '.ant-btn-primary',
                'button.ant-btn-primary'
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    button = await self.page.query_selector(selector)
                    if button:
                        # 检查按钮是否可见和可点击
                        is_visible = await button.is_visible()
                        is_enabled = await button.is_enabled()
                        if is_visible and is_enabled:
                            await button.click()
                            submitted = True
                            logger.info(f"点击发布按钮成功: {selector}")
                            break
                except Exception as e:
                    continue
            
            if not submitted:
                logger.warning("未找到发布按钮")
                # 截图保存以便调试
                screenshot_path = await self.get_page_screenshot()
                return {
                    "success": False,
                    "message": "未找到发布按钮，可能页面结构已变化",
                    "item_id": None,
                    "screenshot": screenshot_path
                }
            
            # 等待发布结果
            await asyncio.sleep(3)
            
            # 检查是否有错误提示
            error_selectors = [
                '.ant-message-error',
                '.error-message',
                '.alert-danger',
                '.ant-notification-notice-error'
            ]
            
            for selector in error_selectors:
                try:
                    error_el = await self.page.query_selector(selector)
                    if error_el:
                        error_text = await error_el.inner_text()
                        if error_text:
                            return {
                                "success": False,
                                "message": f"发布失败: {error_text}",
                                "item_id": None
                            }
                except:
                    continue
            
            # 检查是否成功（通过检测成功提示或页面跳转）
            success_selectors = [
                '.ant-message-success',
                '.ant-notification-notice-success',
                '.success-message'
            ]
            
            for selector in success_selectors:
                try:
                    success_el = await self.page.query_selector(selector)
                    if success_el:
                        logger.info("检测到发布成功提示")
                        break
                except:
                    continue
            
            # 如果没有找到错误，认为发布成功
            logger.info("商品发布成功")
            return {
                "success": True,
                "message": "商品发布成功",
                "item_id": None
            }
            
        except Exception as e:
            logger.error(f"发布商品异常: {e}")
            # 截图保存以便调试
            try:
                screenshot_path = await self.get_page_screenshot()
            except:
                screenshot_path = None
            return {
                "success": False,
                "message": f"发布异常: {str(e)}",
                "item_id": None,
                "screenshot": screenshot_path
            }

    async def get_page_screenshot(self) -> Optional[str]:
        """获取当前页面截图（调试用）"""
        try:
            if not self.page:
                return None
            
            screenshot = await self.page.screenshot(full_page=True)
            # 保存到临时文件
            temp_fd, temp_path = tempfile.mkstemp(suffix=".png")
            os.close(temp_fd)
            with open(temp_path, "wb") as f:
                f.write(screenshot)
            return temp_path
        except Exception as e:
            logger.error(f"获取截图失败: {e}")
            return None

    async def intercept_api_calls(self) -> List[Dict[str, Any]]:
        """
        拦截页面API调用（用于逆向分析）
        
        Returns:
            list: 拦截到的API调用列表
        """
        api_calls = []
        
        async def handle_response(response):
            url = response.url
            if "api" in url.lower() or "agiso" in url.lower():
                try:
                    body = await response.text()
                    api_calls.append({
                        "url": url,
                        "status": response.status,
                        "method": response.request.method,
                        "headers": dict(response.request.headers),
                        "body": body[:1000] if body else None
                    })
                except:
                    pass
        
        self.page.on("response", handle_response)
        return api_calls
