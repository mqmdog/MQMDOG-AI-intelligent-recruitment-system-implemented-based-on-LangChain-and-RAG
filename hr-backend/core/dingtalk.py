import json
from datetime import datetime
from urllib.parse import quote, urljoin

import httpx
from loguru import logger

from settings import settings
from utils.iso8601 import datetime_to_iso8601_beijing # ISO-8601 时间格式转换


class DingTalkApi:
    """钉钉 API URL 构建器"""
    dingtalk_api_base_url: str = "https://api.dingtalk.com"

    @classmethod
    def build_access_token_url(cls) -> str:
        return urljoin(cls.dingtalk_api_base_url, "/v1.0/oauth2/userAccessToken")

    @classmethod
    def build_get_my_info_url(cls) -> str:
        return urljoin(cls.dingtalk_api_base_url, "/v1.0/contact/users/me")

    @classmethod
    def build_get_calendar_list_url(
        cls, union_id: str, time_min: datetime, time_max: datetime,
    ) -> str:
        time_min_encoded = quote(datetime_to_iso8601_beijing(time_min))
        time_max_encoded = quote(datetime_to_iso8601_beijing(time_max))
        path = (
            f"/v1.0/calendar/users/{union_id}/calendars/primary/events"
            f"?timeMin={time_min_encoded}&timeMax={time_max_encoded}"
        )
        return urljoin(cls.dingtalk_api_base_url, path)

    @classmethod
    def build_create_calendar_url(cls, union_id: str) -> str:
        path = f"/v1.0/calendar/users/{union_id}/calendars/primary/events"
        return urljoin(cls.dingtalk_api_base_url, path)


class DingTalkHttp:
    """钉钉 HTTP 请求客户端"""

    async def refresh_access_token(self, refresh_token: str) -> tuple[str, str]:
        """刷新 access_token，返回 (refresh_token, access_token)"""
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                url=DingTalkApi.build_access_token_url(),
                json={
                    "clientId": settings.DINGTALK_CLIENT_ID,
                    "clientSecret": settings.DINGTALK_CLIENT_SECRET,
                    "refreshToken": refresh_token,
                    "grantType": "refresh_token",
                }
            )
            if token_resp.status_code != 200:
                try:
                    error_data = token_resp.json()
                    request_id = error_data.get("requestid", "UNKNOWN")
                    error_code = error_data.get("code", "UNKNOWN")
                    error_msg = error_data.get("message", "UNKNOWN")
                    logger.error(
                        f"Token刷新失败 [requestid={request_id}] [code={error_code}] [message={error_msg}]")
                    raise ValueError(
                        f"Token刷新失败!requestid={request_id},code={error_code},message={error_msg}")
                except json.JSONDecodeError:
                    logger.error(f"Token刷新失败: {token_resp.text}")
                    raise ValueError(f"Token刷新失败!{token_resp.text}")
            token_data = token_resp.json() or {}
            access_token = token_data.get("accessToken")
            refresh_token = token_data.get("refreshToken")
            return refresh_token, access_token

    async def get_calendar_list(
        self, union_id: str, access_token: str, time_min: datetime, time_max: datetime,
    ) -> list[dict]:
        url = DingTalkApi.build_get_calendar_list_url(
            union_id, time_min, time_max)
        headers = {
            "x-acs-dingtalk-access-token": access_token
        }
        async with httpx.AsyncClient() as client:
            calendar_resp = await client.get(url, headers=headers)
            calendar_resp.raise_for_status()
            calendar_data = calendar_resp.json() or {}
            events = calendar_data.get("events")
            return events

    async def create_calendar(
        self, union_id: str, access_token: str, summary: str,
        start_datetime: datetime, end_datetime: datetime,
    ) -> dict:
        url = DingTalkApi.build_create_calendar_url(union_id)
        headers = {
            "x-acs-dingtalk-access-token": access_token
        }
        data = {
            "summary": summary,
            "start": {
                "dateTime": datetime_to_iso8601_beijing(start_datetime),
                "timeZone": "Asia/Shanghai",
            },
            "end": {
                "dateTime": datetime_to_iso8601_beijing(end_datetime),
                "timeZone": "Asia/Shanghai",
            }
        }
        # 创建日程
        async with httpx.AsyncClient() as client:
            calendar_response = await client.post(url, json=data, headers=headers)
            calendar_response.raise_for_status()
            calendar_data = calendar_response.json() or {}
            return calendar_data
