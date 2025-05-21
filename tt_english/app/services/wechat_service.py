
#! 此文件用于模拟微信提供的api
# app/services/wechat_service.py
import httpx
import uuid # 用于生成模拟数据
from typing import Dict, Any
from fastapi import HTTPException, status

from app.core.config import settings

class WeChatService:
    async def code_to_session(self, code: str) -> Dict[str, Any]:
        if settings.MOCK_WECHAT_API:
            return await self._mock_code_to_session(code)
        else:
            return await self._real_code_to_session(code)

    async def _real_code_to_session(self, code: str) -> Dict[str, Any]:
        if not settings.WECHAT_APPID or not settings.WECHAT_APPSECRET:
            # 如果配置了使用真实 API 但未提供 AppID 或 AppSecret，则抛出异常
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="微信 AppID 或 AppSecret 未配置，无法调用真实API。"
            )

        params = {
            "appid": settings.WECHAT_APPID,
            "secret": settings.WECHAT_APPSECRET,
            "js_code": code,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("https://api.weixin.qq.com/sns/jscode2session", params=params)
                response.raise_for_status() # 如果HTTP状态码是4xx或5xx，则抛出异常
                wechat_data = response.json()

                # 对微信返回结果的基本校验
                if "errcode" in wechat_data and wechat_data["errcode"] != 0:
                    # 记录错误信息以便调试
                    print(f"微信 API 错误: {wechat_data}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"微信 API 错误: {wechat_data.get('errmsg', '未知错误')}"
                    )
                if "openid" not in wechat_data:
                    print(f"微信 API 错误: 'openid' 未在响应中 - {wechat_data}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="从微信获取 openid 失败 (响应格式错误)。"
                    )
                return wechat_data
            except httpx.HTTPStatusError as exc:
                # 尽可能记录微信返回的实际错误信息
                error_detail = f"连接微信 API 出错: {exc.response.status_code}"
                try:
                    error_detail += f" - {exc.response.json()}"
                except Exception:
                    error_detail += f" - {exc.response.text}"
                print(error_detail)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)
            except httpx.RequestError as exc:
                print(f"请求微信 API 失败: {exc}")
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"请求微信 API 失败: {exc}")


    async def _mock_code_to_session(self, code: str) -> Dict[str, Any]:
        """
        模拟微信 code2Session API 调用，用于测试。
        你可以根据 'code' 返回不同的 openid 来测试不同场景
        （例如，新用户、已存在用户、无效 code）。
        """
        print(f"--- 调用模拟微信 API，code: {code} ---")
        if code == "invalid_mock_code":
            return {"errcode": 40029, "errmsg": "无效的code (模拟错误)"}
        
        # if code == "test_code_new_user":
        #     mock_openid = f"mock_openid_new_{uuid.uuid4().hex[:10]}"
        # elif code == "test_code_existing_user_1":
        #     mock_openid = "mock_openid_existing_001" # 用于测试已存在用户的固定 openid
        # elif code == "test_code_existing_user_2":
        #     mock_openid = "mock_openid_existing_002"
        # else:
        #     # 默认行为：根据 code 生成一个 唯一的 openid
        #     mock_openid = f"mock_openid_for_{code}_{uuid.uuid4().hex[:6]}"

        mock_openid = f"mock_openid_for_{code}_"

        mock_session_key = f"mock_session_key_{uuid.uuid4().hex[:10]}"
        
        return {
            "openid": mock_openid,
            "session_key": mock_session_key,
            # "unionid": "mock_unionid_..." # 如果你计划使用 unionid
        }

# 你可以创建一个实例方便导入，或者使用 Depends 注入
wechat_service = WeChatService()