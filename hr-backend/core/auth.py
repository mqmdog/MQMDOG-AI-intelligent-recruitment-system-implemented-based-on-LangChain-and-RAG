import jwt
from datetime import datetime
from enum import Enum

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from core.single import SingletonMeta
from settings import settings


# 访问令牌和刷新令牌
class TokenTypeEnum(Enum):
    ACCESS_TOKEN = 1
    REFRESH_TOKEN = 2


class AuthHandler(metaclass=SingletonMeta):  # 单例，避免重复加载密钥、重复初始化
    """JWT 认证处理器（单例）"""

    security = HTTPBearer()  # FastAPI的Bearer认证依赖
    secret = settings.JWT_SECRET_KEY

    # 编码令牌
    def _encode_token(self, iss: str, token_type: TokenTypeEnum) -> str:
        # 构造payload
        payload = {
            "iss": iss,  # 用户ID
            "sub": str(token_type.value),  # token类型（1=access, 2=refresh）
        }
        # 添加过期时间
        if token_type == TokenTypeEnum.ACCESS_TOKEN:
            exp = datetime.now() + settings.JWT_ACCESS_TOKEN_EXPIRES
        else:
            exp = datetime.now() + settings.JWT_REFRESH_TOKEN_EXPIRES
        payload["exp"] = int(exp.timestamp()) 
        # 签名并返回token
        return jwt.encode(payload, self.secret, algorithm="HS256")

    # 登录时生成
    def encode_login_token(self, iss: str) -> dict[str, str]:
        return {
            "access_token": self._encode_token(iss, TokenTypeEnum.ACCESS_TOKEN),
            "refresh_token": self._encode_token(iss, TokenTypeEnum.REFRESH_TOKEN),
        }

    # 更新令牌时生成，只刷新access
    def encode_update_token(self, iss: str) -> dict[str, str]:
        return {
            "access_token": self._encode_token(iss, TokenTypeEnum.ACCESS_TOKEN),
        }

    # 解码令牌
    def decode_access_token(self, token: str) -> str:
        try:
            # 解码token
            payload = jwt.decode(token, self.secret, algorithms=["HS256"])
            # 验证token类型
            if payload["sub"] != str(TokenTypeEnum.ACCESS_TOKEN.value):
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Token类型错误！")
            # 返回用户ID
            return payload["iss"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="Access Token已过期！")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="Access Token不可用！")

    # 验证刷新令牌
    def decode_refresh_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self.secret, algorithms=["HS256"])
            if payload["sub"] != str(TokenTypeEnum.REFRESH_TOKEN.value):
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED, detail="Token类型错误！")
            return payload["iss"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, detail="Refresh Token已过期！")
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, detail="Refresh Token不可用！")

    # 访问令牌依赖
    def auth_access_dependency(self, auth: HTTPAuthorizationCredentials = Security(security)) -> str:
        # auth.credentials 是从请求头Authorization中提取的token
        return self.decode_access_token(auth.credentials)

    # 刷新令牌依赖
    def auth_refresh_dependency(self, auth: HTTPAuthorizationCredentials = Security(security)) -> str:
        return self.decode_refresh_token(auth.credentials)
