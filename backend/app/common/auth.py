import jwt
from functools import wraps
from datetime import datetime, timezone, timedelta
from flask import request, current_app

from .response import fail


def create_token(payload=None):
    """签发 JWT"""
    if payload is None:
        payload = {}
    expires = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
    payload.update({
        "exp": datetime.now(timezone.utc) + timedelta(seconds=expires),
        "iat": datetime.now(timezone.utc),
    })
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm="HS256")


def verify_token(token):
    """验证 JWT，返回 payload 或 None"""
    try:
        return jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def login_required(f):
    """认证装饰器：要求请求携带有效的 JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return fail("未提供认证令牌", 401)

        token = auth_header[7:]
        payload = verify_token(token)
        if payload is None:
            return fail("认证令牌无效或已过期", 401)

        return f(*args, **kwargs)
    return decorated
