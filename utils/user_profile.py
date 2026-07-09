#!/usr/bin/env python3
"""
闲鱼用户资料获取工具
用于获取用户昵称和头像
"""

import json
import time
import hashlib
from typing import Optional, Dict, Any
import httpx
from loguru import logger
from .xianyu_utils import trans_cookies, generate_sign


class UserProfileFetcher:
    """闲鱼用户资料获取器"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Referer': 'https://www.goofish.com/',
            'Origin': 'https://www.goofish.com',
        }
        self.timeout = httpx.Timeout(connect=30.0, read=60.0, write=30.0, pool=60.0)

    async def get_user_profile(self, cookies_str: str) -> Optional[Dict[str, Any]]:
        """获取用户资料（昵称和头像）
        
        Args:
            cookies_str: Cookie字符串
            
        Returns:
            包含nickname和avatar_url的字典，失败返回None
        """
        try:
            # 解析Cookie
            cookies_dict = trans_cookies(cookies_str)
            unb = cookies_dict.get('unb')
            
            if not unb:
                logger.error("Cookie中缺少unb字段")
                return None

            # 获取m_h5_tk用于签名
            m_h5_tk = cookies_dict.get('_m_h5_tk', '')
            token = m_h5_tk.split('_')[0] if '_' in m_h5_tk else ''
            
            if not token:
                logger.warning("Cookie中缺少m_h5_tk，尝试获取...")
                # 尝试获取m_h5_tk
                token = await self._get_m_h5_tk(cookies_dict)
                if not token:
                    logger.error("无法获取m_h5_tk")
                    return None

            # 构造请求参数
            t = str(int(time.time() * 1000))
            app_key = "34839810"
            
            # 尝试多个可能的API端点
            api_endpoints = [
                'mtop.idle.web.xyh.info',
                'mtop.idle.user.profile',
                'mtop.taobao.user.get',
            ]
            
            for api_name in api_endpoints:
                try:
                    result = await self._call_api(api_name, unb, t, token, app_key, cookies_dict)
                    if result:
                        logger.info(f"获取用户资料成功: {api_name}")
                        return result
                except Exception as e:
                    logger.debug(f"API {api_name} 调用失败: {e}")
                    continue
            
            logger.error("所有用户资料API都失败")
            return None

        except Exception as e:
            logger.error(f"获取用户资料异常: {e}")
            return None

    async def _get_m_h5_tk(self, cookies_dict: Dict[str, str]) -> Optional[str]:
        """获取m_h5_tk"""
        try:
            api_url = "https://h5api.m.goofish.com/h5/mtop.gaia.nodejs.gaia.idle.data.gw.v2.index.get/1.0/"
            
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                # 先发一次请求获取cookie中的m_h5_tk
                resp = await client.get(api_url, headers=self.headers, cookies=cookies_dict)
                new_cookies = dict(resp.cookies)
                
                m_h5_tk = new_cookies.get("m_h5_tk", "")
                if m_h5_tk:
                    token = m_h5_tk.split("_")[0] if "_" in m_h5_tk else ""
                    return token
                
                return None
        except Exception as e:
            logger.error(f"获取m_h5_tk失败: {e}")
            return None

    async def _call_api(self, api_name: str, unb: str, t: str, token: str, app_key: str, cookies_dict: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """调用闲鱼API"""
        api_url = f"https://h5api.m.goofish.com/h5/{api_name}/1.0/"
        
        # 构造请求数据
        data = {"userId": unb}
        data_str = json.dumps(data, separators=(',', ':'))
        
        # 生成签名
        sign = generate_sign(t, token, data_str)
        
        # 构造请求参数
        params = {
            'jsv': '2.7.2',
            'appKey': app_key,
            't': t,
            'sign': sign,
            'v': '1.0',
            'type': 'originaljson',
            'accountSite': 'xianyu',
            'dataType': 'json',
            'timeout': '20000',
            'api': api_name,
            'sessionOption': 'AutoLoginOnly',
        }
        
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            resp = await client.post(
                api_url,
                params=params,
                data={'data': data_str},
                headers=self.headers,
                cookies=cookies_dict
            )
            
            result = resp.json()
            
            # 检查API响应
            if result.get('ret', [])[0].startswith('SUCCESS'):
                data = result.get('data', {})
                
                # 尝试从不同的API响应格式中提取用户信息
                user_info = self._extract_user_info(data)
                if user_info:
                    return user_info
            
            logger.debug(f"API {api_name} 响应: {result}")
            return None

    def _extract_user_info(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从API响应中提取用户信息"""
        # 尝试不同的数据结构
        user_data = None
        
        # 结构1: data.user
        if 'user' in data:
            user_data = data['user']
        # 结构2: data.userInfo
        elif 'userInfo' in data:
            user_data = data['userInfo']
        # 结构3: data.data.user
        elif 'data' in data and 'user' in data['data']:
            user_data = data['data']['user']
        # 结构4: 直接在data中
        elif 'nick' in data or 'nickname' in data:
            user_data = data
        
        if not user_data:
            return None
        
        # 提取昵称
        nickname = (
            user_data.get('nick') or
            user_data.get('nickname') or
            user_data.get('userName') or
            user_data.get('name') or
            ''
        )
        
        # 提取头像
        avatar_url = (
            user_data.get('avatar') or
            user_data.get('avatarUrl') or
            user_data.get('headUrl') or
            user_data.get('picUrl') or
            ''
        )
        
        if nickname or avatar_url:
            return {
                'nickname': nickname,
                'avatar_url': avatar_url
            }
        
        return None


# 全局实例
user_profile_fetcher = UserProfileFetcher()


async def get_user_profile_from_cookies(cookies_str: str) -> Optional[Dict[str, Any]]:
    """从Cookie获取用户资料的便捷函数"""
    return await user_profile_fetcher.get_user_profile(cookies_str)
