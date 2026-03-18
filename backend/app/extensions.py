from pymongo import MongoClient
from redis import Redis
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


class Mongo:
    """MongoDB 容器，支持 from app.extensions import mongo 后通过 mongo.db 访问"""
    client: MongoClient = None
    db = None

mongo = Mongo()


class RedisExt:
    """Redis 容器"""
    client: Redis = None

redis_ext = RedisExt()

# SocketIO
socketio = SocketIO(cors_allowed_origins="*")

# CORS
cors = CORS()

# 限速器
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


def init_extensions(app):
    """初始化所有扩展"""
    # MongoDB
    mongo.client = MongoClient(app.config['MONGO_URI'])
    db_name = app.config['MONGO_URI'].rsplit('/', 1)[-1].split('?')[0] or 'infohub'
    mongo.db = mongo.client[db_name]

    # Redis
    redis_ext.client = Redis.from_url(app.config['REDIS_URL'], decode_responses=True)

    # Flask 扩展
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    socketio.init_app(app)
    if not app.config.get('TESTING'):
        app.config['RATELIMIT_STORAGE_URI'] = app.config['REDIS_URL']
    limiter.init_app(app)
