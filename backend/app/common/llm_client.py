"""LLM API 统一封装 —— 所有模块通过此类调用 AI 服务。
使用 openai 库（DeepSeek API 兼容 OpenAI 格式）。
"""

import os
import logging

from openai import OpenAI

logger = logging.getLogger(__name__)

# 从环境变量读取配置
_api_key = os.getenv("LLM_API_KEY", "")
_api_base = os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1")
_model = os.getenv("LLM_MODEL", "deepseek-chat")

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=_api_key, base_url=_api_base, timeout=60)
    return _client


class LLMClient:
    """统一的 LLM 调用入口。"""

    def summarize(self, text: str, max_length: int = 200) -> str:
        """生成中文摘要（200字以内）。"""
        if not text or not text.strip():
            raise ValueError("文章内容为空，无法生成摘要")

        # 截断过长的正文，避免超出 token 限制
        truncated = text[:6000]

        system_prompt = (
            "你是一个专业的信息摘要助手。请用简洁的中文总结以下文章的核心内容，"
            f"摘要控制在{max_length}字以内，直接输出摘要内容，不要加任何前缀。"
        )

        try:
            resp = _get_client().chat.completions.create(
                model=_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": truncated},
                ],
                max_tokens=500,
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error("LLM summarize failed: %s", e)
            raise

    def chat(self, messages: list, system_prompt: str = None, stream: bool = False):
        """对话接口（支持流式）。

        Parameters
        ----------
        messages : list[dict]
            对话消息列表，每条 {"role": "user"|"assistant", "content": "..."}
        system_prompt : str, optional
            系统提示词
        stream : bool
            是否流式返回

        Returns
        -------
        str | generator
            非流式：返回完整回复文本
            流式：返回 generator，每次 yield 一段文本 chunk
        """
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        try:
            resp = _get_client().chat.completions.create(
                model=_model,
                messages=msgs,
                max_tokens=2000,
                temperature=0.7,
                stream=stream,
            )

            if stream:
                return self._stream_iter(resp)
            else:
                return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error("LLM chat failed: %s", e)
            raise

    @staticmethod
    def _stream_iter(resp):
        """将流式响应转换为文本 chunk 生成器。"""
        for chunk in resp:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# 模块级单例
llm_client = LLMClient()
