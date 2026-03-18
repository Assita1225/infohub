"""Trending 定时抓取任务（可由 Celery Beat 调度）"""
import logging

logger = logging.getLogger(__name__)


def refresh_all_trending():
    """
    定时任务入口：刷新所有热榜来源。
    由 Celery Beat 每 30 分钟调用一次，也可手动触发。
    """
    from .services import refresh_all_sources
    results = refresh_all_sources()
    total = sum(r["count"] for r in results)
    errors = [r for r in results if r["error"]]
    logger.info(f"热榜定时刷新完成: 共 {total} 条, {len(errors)} 个源失败")
    return results
