from flask import request

from app.extensions import limiter
from app.common.response import success, fail
from app.common.auth import login_required, create_token
from . import auth_bp
from .services import is_password_set, setup_password, verify_password, change_password


@auth_bp.route('/status', methods=['GET'])
def status():
    """检查是否已设置密码"""
    return success({"initialized": is_password_set()})


@auth_bp.route('/setup', methods=['POST'])
def setup():
    """首次设置密码（仅允许调用一次）"""
    if is_password_set():
        return fail("密码已设置，不可重复设置", 403)

    data = request.get_json(silent=True) or {}
    password = data.get('password', '').strip()
    if len(password) < 6:
        return fail("密码长度不能少于 6 位", 400, errors={"password": "至少 6 个字符"})

    setup_password(password)
    token = create_token({"sub": "owner"})
    return success({"token": token}, "密码设置成功")


@auth_bp.route('/unlock', methods=['POST'])
@limiter.limit("5/minute")
def unlock():
    """验证密码，返回 JWT"""
    if not is_password_set():
        return fail("尚未设置密码，请先调用 /api/auth/setup", 400)

    data = request.get_json(silent=True) or {}
    password = data.get('password', '')
    if not verify_password(password):
        return fail("密码错误", 401)

    token = create_token({"sub": "owner"})
    return success({"token": token}, "解锁成功")


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_pwd():
    """修改密码"""
    data = request.get_json(silent=True) or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '').strip()

    if len(new_password) < 6:
        return fail("新密码长度不能少于 6 位", 400, errors={"new_password": "至少 6 个字符"})

    ok, err = change_password(old_password, new_password)
    if not ok:
        return fail(err, 400)

    token = create_token({"sub": "owner"})
    return success({"token": token}, "密码修改成功")
