from celery import Celery
from celery.schedules import crontab

from app import create_app

flask_app = create_app()

# 创建 Celery 实例
celery_app = Celery(
    'infohub',
    broker=flask_app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    backend=flask_app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2'),
)

celery_app.conf.update(
    timezone='Asia/Shanghai',
    enable_utc=True,
)

# Celery Beat 定时任务
celery_app.conf.beat_schedule = {
    'refresh-trending-every-30min': {
        'task': 'celery_worker.task_refresh_trending',
        'schedule': crontab(minute='*/30'),  # 每 30 分钟
    },
}


@celery_app.task(name='celery_worker.task_refresh_trending')
def task_refresh_trending():
    """定时刷新热榜数据"""
    with flask_app.app_context():
        from app.trending.tasks import refresh_all_trending
        return refresh_all_trending()
