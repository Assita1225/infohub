from flask import jsonify


class AppError(Exception):
    """业务异常基类"""
    def __init__(self, message, code=400, errors=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.errors = errors


def register_error_handlers(app):
    """注册全局错误处理器"""

    @app.errorhandler(AppError)
    def handle_app_error(e):
        body = {"code": e.code, "data": None, "message": e.message}
        if e.errors:
            body["errors"] = e.errors
        return jsonify(body), e.code

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"code": 404, "data": None, "message": "资源不存在"}), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({"code": 405, "data": None, "message": "方法不允许"}), 405

    @app.errorhandler(500)
    def handle_500(e):
        return jsonify({"code": 500, "data": None, "message": "服务器内部错误"}), 500
