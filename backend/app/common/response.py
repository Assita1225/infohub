from flask import jsonify


def success(data=None, message="success", code=200):
    """统一成功响应"""
    return jsonify({
        "code": code,
        "data": data,
        "message": message,
    }), code


def paginated(items, total, page, page_size, message="success"):
    """统一分页响应"""
    return jsonify({
        "code": 200,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        "message": message,
    }), 200


def fail(message="error", code=400, errors=None):
    """统一失败响应"""
    body = {
        "code": code,
        "data": None,
        "message": message,
    }
    if errors:
        body["errors"] = errors
    return jsonify(body), code
