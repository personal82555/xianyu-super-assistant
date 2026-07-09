"""
AI回复引擎模块
集成XianyuAutoAgent的AI回复功能到现有项目中
"""

import os
import json
import time
import hashlib
import sqlite3
from typing import List, Dict, Optional
from loguru import logger
from openai import OpenAI
from db_manager import db_manager


class AIReplyEngine:
    """AI回复引擎"""
    
    def __init__(self):
        self.clients = {}  # 存储不同账号的OpenAI客户端
        self.agents = {}   # 存储不同账号的Agent实例
        self._cache = {}   # AI回复缓存 {cache_key: (reply, expiry)}
        self._intent_cache = {}  # 意图缓存 {cache_key: (intent, expiry)}
        self._cache_ttl = 3600  # 缓存有效期1小时
        self._init_default_prompts()

    def _make_cache_key(self, cookie_id: str, chat_id: str, message: str) -> str:
        """生成缓存键"""
        raw = f"{cookie_id}|{chat_id}|{message}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _get_cached_reply(self, cookie_id: str, chat_id: str, message: str) -> Optional[str]:
        """获取缓存的AI回复"""
        key = self._make_cache_key(cookie_id, chat_id, message)
        cached = self._cache.get(key)
        if cached and time.time() < cached[1]:
            logger.info(f"命中AI回复缓存 (账号: {cookie_id})")
            return cached[0]
        if cached:
            del self._cache[key]
        return None

    def _set_cached_reply(self, cookie_id: str, chat_id: str, message: str, reply: str):
        """设置AI回复缓存"""
        key = self._make_cache_key(cookie_id, chat_id, message)
        self._cache[key] = (reply, time.time() + self._cache_ttl)

    def _get_cached_intent(self, cookie_id: str, message: str) -> Optional[str]:
        """获取缓存的意图"""
        key = self._make_cache_key(cookie_id, "", message)
        cached = self._intent_cache.get(key)
        if cached and time.time() < cached[1]:
            return cached[0]
        if cached:
            del self._intent_cache[key]
        return None

    def _set_cached_intent(self, cookie_id: str, message: str, intent: str):
        """设置意图缓存"""
        key = self._make_cache_key(cookie_id, "", message)
        self._intent_cache[key] = (intent, time.time() + self._cache_ttl)
    
    def _init_default_prompts(self):
        """初始化默认提示词"""
        self.default_prompts = {
            'classify': '''你是一个意图分类专家，需要判断用户消息的意图类型。
请根据用户消息内容，返回以下意图之一：
- price: 价格相关（议价、优惠、降价等）
- tech: 技术相关（产品参数、使用方法、故障等）
- refund: 退款相关（申请退款、退货、投诉等）
- default: 其他一般咨询

只返回意图类型，不要其他内容。''',
            
            'price': '''你是一位经验丰富的销售专家，擅长议价。
语言要求：简短直接，每句≤10字，总字数≤40字。
议价策略：
1. 根据议价次数递减优惠：第1次小幅优惠，第2次中等优惠，第3次最大优惠
2. 接近最大议价轮数时要坚持底线，强调商品价值
3. 优惠不能超过设定的最大百分比和金额
4. 语气要友好但坚定，突出商品优势
注意：结合商品信息、对话历史和议价设置，给出合适的回复。''',
            
            'tech': '''你是一位技术专家，专业解答产品相关问题。
语言要求：简短专业，每句≤10字，总字数≤40字。
回答重点：产品功能、使用方法、注意事项。
注意：基于商品信息回答，避免过度承诺。''',
            
            'refund': '''你是一位售后客服，处理用户的退款退货请求。
语言要求：礼貌耐心，语气温和，每句≤15字，总字数≤60字。
注意：请严格遵循【退款策略】指示。''',

            'default': '''你是一位资深电商卖家，提供优质客服。
语言要求：简短友好，每句≤10字，总字数≤40字。
回答重点：商品介绍、物流、售后等常见问题。
注意：结合商品信息，给出实用建议。'''
        }
    
    def get_client(self, cookie_id: str) -> Optional[OpenAI]:
        """获取指定账号的OpenAI客户端"""
        if cookie_id not in self.clients:
            settings = db_manager.get_ai_reply_settings(cookie_id)
            if not settings['ai_enabled']:
                logger.warning(f"AI回复未启用 (账号: {cookie_id})")
                return None
            if not settings['api_key']:
                logger.warning(f"AI回复的 API Key 未配置 (账号: {cookie_id})")
                return None
            
            try:
                self.clients[cookie_id] = OpenAI(
                    api_key=settings['api_key'],
                    base_url=settings['base_url'],
                    timeout=60
                )
                logger.info(f"为账号 {cookie_id} 创建OpenAI客户端")
            except Exception as e:
                logger.error(f"创建OpenAI客户端失败 {cookie_id}: {e}")
                return None
        
        return self.clients[cookie_id]
    
    def is_ai_enabled(self, cookie_id: str) -> bool:
        """检查指定账号是否启用AI回复"""
        settings = db_manager.get_ai_reply_settings(cookie_id)
        return settings['ai_enabled']
    
    def detect_intent(self, message: str, cookie_id: str) -> str:
        """检测用户消息意图（带缓存）"""
        cached = self._get_cached_intent(cookie_id, message)
        if cached:
            return cached

        client = self.get_client(cookie_id)
        if not client:
            return 'default'
        
        try:
            settings = db_manager.get_ai_reply_settings(cookie_id)
            custom_prompts = json.loads(settings['custom_prompts']) if settings['custom_prompts'] else {}
            classify_prompt = custom_prompts.get('classify', self.default_prompts['classify'])
            
            response = client.chat.completions.create(
                model=settings['model_name'],
                messages=[
                    {"role": "system", "content": classify_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            raw_content = response.choices[0].message.content
            intent = raw_content.strip().lower() if raw_content else 'default'
            if intent not in ['price', 'tech', 'refund', 'default']:
                intent = 'default'

            self._set_cached_intent(cookie_id, message, intent)
            return intent
                
        except Exception as e:
            logger.error(f"意图检测失败 {cookie_id}: {e}")
            return 'default'
    
    def generate_reply(self, message: str, item_info: dict, chat_id: str, 
                      cookie_id: str, user_id: str, item_id: str) -> Optional[str]:
        """生成AI回复（带缓存，带重试）"""
        if not self.is_ai_enabled(cookie_id):
            return None

        # 检查缓存
        cached_reply = self._get_cached_reply(cookie_id, chat_id, message)
        if cached_reply:
            return cached_reply

        client = self.get_client(cookie_id)
        if not client:
            logger.warning(f"生成AI回复失败: 无法获取 OpenAI 客户端 (账号: {cookie_id})")
            return None
        
        # 获取设置（重试参数也放在 settings 里）
        try:
            settings = db_manager.get_ai_reply_settings(cookie_id)
        except Exception as e:
            logger.error(f"获取AI回复设置失败 {cookie_id}: {e}")
            return None

        # 读取重试配置
        max_retry = 3
        retry_interval = 5

        # 检测意图
        intent = self.detect_intent(message, cookie_id)
        logger.info(f"检测到意图: {intent} (账号: {cookie_id})")

        # 获取对话历史和议价信息（在重试循环外，只做一次）
        context = self.get_conversation_context(chat_id, cookie_id)
        bargain_count = self.get_bargain_count(chat_id, cookie_id)
        refund_policy = settings.get('refund_policy', 'allow')

        # 检查议价轮数限制
        if intent == "price":
            max_bargain_rounds = settings.get('max_bargain_rounds', 3)
            if bargain_count >= max_bargain_rounds:
                logger.info(f"议价次数已达上限 ({bargain_count}/{max_bargain_rounds})，拒绝继续议价")
                refuse_reply = "抱歉，这个价格已经是最优惠的了，不能再便宜了哦！"
                self.save_conversation(chat_id, cookie_id, user_id, item_id, "user", message, intent)
                self.save_conversation(chat_id, cookie_id, user_id, item_id, "assistant", refuse_reply, intent)
                return refuse_reply

        # 构建提示词相关（在重试循环外，只做一次）
        custom_prompts = json.loads(settings['custom_prompts']) if settings.get('custom_prompts') else {}
        system_prompt = custom_prompts.get(intent, self.default_prompts[intent])

        item_desc = f"商品标题: {item_info.get('title', '未知')}\n"
        item_desc += f"商品价格: {item_info.get('price', '未知')}元\n"
        item_desc += f"商品描述: {item_info.get('desc', '无')}"

        context_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context[-10:]])
        max_bargain_rounds = settings.get('max_bargain_rounds', 3)
        max_discount_percent = settings.get('max_discount_percent', 10)
        max_discount_amount = settings.get('max_discount_amount', 100)

        refund_instruction = "" if intent != "refund" else (
            "【退款策略】该商品支持退款，请引导用户通过平台申请退款，告知流程和预计时间。"
            if refund_policy == "allow"
            else "【退款策略】该商品不支持退款，请礼貌说明原因（虚拟商品/已发货/特殊商品等），并表示歉意。"
        )

        user_prompt = f"""商品信息：
{item_desc}

对话历史：
{context_str}

议价设置：
- 当前议价次数：{bargain_count}
- 最大议价轮数：{max_bargain_rounds}
- 最大优惠百分比：{max_discount_percent}%
- 最大优惠金额：{max_discount_amount}元

{refund_instruction}

用户消息：{message}

请根据以上信息生成回复："""

        # === 带重试的 API 调用 ===
        last_error = None
        for attempt in range(max_retry):
            try:
                response = client.chat.completions.create(
                    model=settings['model_name'],
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=2048,
                    temperature=0.7
                )

                raw_reply = response.choices[0].message.content
                if not raw_reply:
                    raise ValueError("AI 返回内容为空")
                reply = raw_reply.strip()

                # 保存对话记录
                self.save_conversation(chat_id, cookie_id, user_id, item_id, "user", message, intent)
                self.save_conversation(chat_id, cookie_id, user_id, item_id, "assistant", reply, intent)

                # 更新议价次数
                if intent == "price":
                    self.increment_bargain_count(chat_id, cookie_id)

                # 写入缓存
                self._set_cached_reply(cookie_id, chat_id, message, reply)

                logger.info(f"AI回复生成成功 (账号: {cookie_id}): {reply}")
                return reply

            except Exception as e:
                last_error = e
                if attempt < max_retry - 1:
                    logger.warning(f"AI回复生成失败 (第{attempt + 1}/{max_retry}次重试) {cookie_id}: {e}")
                    time.sleep(retry_interval)
                else:
                    logger.error(f"AI回复生成失败 (已重试{max_retry}次) {cookie_id}: {e}")

        return None
    
    def get_conversation_context(self, chat_id: str, cookie_id: str, limit: int = 20) -> List[Dict]:
        """获取对话上下文"""
        try:
            with db_manager.lock:
                cursor = db_manager.conn.cursor()
                cursor.execute('''
                SELECT role, content FROM ai_conversations 
                WHERE chat_id = ? AND cookie_id = ? 
                ORDER BY created_at DESC LIMIT ?
                ''', (chat_id, cookie_id, limit))
                
                results = cursor.fetchall()
                # 反转顺序，使其按时间正序
                context = [{"role": row[0], "content": row[1]} for row in reversed(results)]
                return context
        except Exception as e:
            logger.error(f"获取对话上下文失败: {e}")
            return []
    
    def save_conversation(self, chat_id: str, cookie_id: str, user_id: str, 
                         item_id: str, role: str, content: str, intent: str = None):
        """保存对话记录"""
        try:
            with db_manager.lock:
                cursor = db_manager.conn.cursor()
                cursor.execute('''
                INSERT INTO ai_conversations 
                (cookie_id, chat_id, user_id, item_id, role, content, intent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (cookie_id, chat_id, user_id, item_id, role, content, intent))
                db_manager.conn.commit()
        except Exception as e:
            logger.error(f"保存对话记录失败: {e}")
    
    def get_bargain_count(self, chat_id: str, cookie_id: str) -> int:
        """获取议价次数"""
        try:
            with db_manager.lock:
                cursor = db_manager.conn.cursor()
                cursor.execute('''
                SELECT COUNT(*) FROM ai_conversations 
                WHERE chat_id = ? AND cookie_id = ? AND intent = 'price' AND role = 'user'
                ''', (chat_id, cookie_id))
                
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"获取议价次数失败: {e}")
            return 0
    
    def increment_bargain_count(self, chat_id: str, cookie_id: str):
        """增加议价次数（通过保存记录自动增加）"""
        # 议价次数通过查询price意图的用户消息数量来计算，无需单独操作
        pass
    
    def clear_cache(self, cookie_id: str = None):
        """清理AI回复和意图缓存"""
        if cookie_id:
            prefix = hashlib.md5(f"{cookie_id}|".encode()).hexdigest()[:8]
            self._cache = {k: v for k, v in self._cache.items() if not k.startswith(prefix)}
            self._intent_cache = {k: v for k, v in self._intent_cache.items() if not k.startswith(prefix)}
            logger.info(f"清理账号 {cookie_id} 的AI回复缓存")
        else:
            self._cache.clear()
            self._intent_cache.clear()
            logger.info("清理所有AI回复缓存")

    def clear_client_cache(self, cookie_id: str = None):
        """清理客户端缓存"""
        if cookie_id:
            self.clients.pop(cookie_id, None)
            logger.info(f"清理账号 {cookie_id} 的客户端缓存")
        else:
            self.clients.clear()
            logger.info("清理所有客户端缓存")


# 全局AI回复引擎实例
ai_reply_engine = AIReplyEngine()
