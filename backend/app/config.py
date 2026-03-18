import os
from dotenv import load_dotenv

# 在类定义前加载 .env，确保 os.getenv 能读到环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))


class Config:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/infohub')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
