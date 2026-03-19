"""统一 HTTP 客户端 —— 根据目标域名自动决定是否走代理"""
import logging
import os
from urllib.parse import urlparse

import feedparser
import requests

logger = logging.getLogger(__name__)

# ── 国内域名列表（命中则 不走代理） ──────────────────────────
DOMESTIC_DOMAINS = {
    "weibo.com",
    "baidu.com",
    "zhihu.com",
    "bilibili.com",
    "douyin.com",
    "toutiao.com",
    "sspai.com",
    "deepseek.com",
    "36kr.com",
    "juejin.cn",
    "csdn.net",
    "163.com",
    "qq.com",
    "sina.com.cn",
    "sohu.com",
    "jianshu.com",
    "douban.com",
    "aliyun.com",
    "taobao.com",
    "jd.com",
}


def _get_proxy_config() -> dict | None:
    """读取环境变量中的代理配置，未配置则返回 None"""
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    if not http_proxy and not https_proxy:
        return None
    return {
        "http": http_proxy or https_proxy,
        "https": https_proxy or http_proxy,
    }


def _is_domestic(url: str) -> bool:
    """判断 URL 是否属于国内域名"""
    hostname = urlparse(url).hostname or ""
    for domain in DOMESTIC_DOMAINS:
        if hostname == domain or hostname.endswith("." + domain):
            return True
    return False


def _get_proxies_for_url(url: str) -> dict | None:
    """根据 URL 返回应使用的代理配置（国内域名返回 None）"""
    proxy_config = _get_proxy_config()
    if proxy_config is None:
        return None
    if _is_domestic(url):
        return None
    return proxy_config


# ── 公开 API ─────────────────────────────────────────────────


def http_get(url: str, **kwargs) -> requests.Response:
    """代理感知的 GET 请求，kwargs 透传给 requests.get"""
    proxies = _get_proxies_for_url(url)
    if proxies:
        kwargs.setdefault("proxies", proxies)
    return requests.get(url, **kwargs)


def http_post(url: str, **kwargs) -> requests.Response:
    """代理感知的 POST 请求，kwargs 透传给 requests.post"""
    proxies = _get_proxies_for_url(url)
    if proxies:
        kwargs.setdefault("proxies", proxies)
    return requests.post(url, **kwargs)


def parse_feed(url: str, **kwargs) -> feedparser.FeedParserDict:
    """代理感知的 feedparser.parse —— 先用 http_get 拿内容再解析"""
    proxies = _get_proxies_for_url(url)
    if proxies:
        # 需要走代理：先用 requests 获取内容，再交给 feedparser 解析
        resp = http_get(url, timeout=kwargs.pop("timeout", 30), **kwargs)
        resp.raise_for_status()
        return feedparser.parse(resp.content)
    # 不走代理：直接让 feedparser 请求
    return feedparser.parse(url)


def get_goose_config() -> dict:
    """返回 Goose3 配置，包含代理设置（如果有）"""
    config = {"browser_user_agent": "InfoHub/1.0 RSS Reader"}
    proxy_config = _get_proxy_config()
    if proxy_config:
        # Goose3 使用 http_proxies 配置项
        config["http_proxies"] = proxy_config
    return config
