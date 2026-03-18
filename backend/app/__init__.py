import os
from flask import Flask

from .config import config_map
from .extensions import init_extensions
from .common.errors import register_error_handlers
from .common.response import success


def create_app(config_name=None):
    """应用工厂函数"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map['development']))

    # 初始化扩展
    init_extensions(app)

    # 注册错误处理
    register_error_handlers(app)

    # 健康检查端点
    @app.route('/api/health')
    def health_check():
        return success({"status": "ok"}, message="InfoHub is running")

    # 注册 Blueprint
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    from .rss import rss_bp
    app.register_blueprint(rss_bp, url_prefix='/api/rss')

    from .notes import notes_bp
    app.register_blueprint(notes_bp, url_prefix='/api/notes')

    from .chat import chat_bp
    app.register_blueprint(chat_bp, url_prefix='/api/chat')

    from .news import news_bp
    app.register_blueprint(news_bp, url_prefix='/api/news')

    from .trending import trending_bp
    app.register_blueprint(trending_bp, url_prefix='/api/trending')

    from .recommend import recommend_bp
    app.register_blueprint(recommend_bp, url_prefix='/api/recommend')

    # 初始化 MongoDB 索引 + 预设数据
    with app.app_context():
        from .notes.services import ensure_text_index
        ensure_text_index()
        from .chat.models import ensure_indexes as ensure_chat_indexes
        ensure_chat_indexes()
        from .news.models import ensure_indexes as ensure_news_indexes, seed_news_sources
        ensure_news_indexes()
        seed_news_sources()
        from .trending.models import ensure_indexes as ensure_trending_indexes
        ensure_trending_indexes()
        from .recommend.models import seed_user_tags
        seed_user_tags()

    return app
