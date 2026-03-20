"""Tools 模块路由 —— 翻译、润色、总结，均支持 SSE 流式输出。"""

import json
import logging

from flask import request, Response, stream_with_context

from . import tools_bp
from .prompts import (
    TRANSLATE_PROMPT, TRANSLATE_AUTO_PROMPT, POLISH_PROMPT, SUMMARIZE_PROMPT,
    LANG_MAP, STYLE_MAP, LENGTH_MAP,
)
from ..common.auth import login_required
from ..common.response import fail
from ..common.llm_client import llm_client

logger = logging.getLogger(__name__)


def _sse_response(system_prompt, user_text):
    """通用 SSE 流式响应生成器。"""

    def generate():
        try:
            messages = [{"role": "user", "content": user_text}]
            for chunk in llm_client.chat(messages, system_prompt=system_prompt, stream=True):
                yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error("Tools SSE stream error: %s", e)
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


@tools_bp.route('/translate', methods=['POST'])
@login_required
def translate():
    """翻译工具（SSE 流式）。"""
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()
    if not text:
        return fail("请输入要翻译的文本")

    source_lang = data.get('source_lang', 'auto')
    target_lang = data.get('target_lang', 'en')

    target_name = LANG_MAP.get(target_lang, target_lang)

    if source_lang == 'auto':
        prompt = TRANSLATE_AUTO_PROMPT.format(target_lang=target_name)
    else:
        source_name = LANG_MAP.get(source_lang, source_lang)
        prompt = TRANSLATE_PROMPT.format(source_lang=source_name, target_lang=target_name)

    return _sse_response(prompt, text)


@tools_bp.route('/polish', methods=['POST'])
@login_required
def polish():
    """文本润色工具（SSE 流式）。"""
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()
    if not text:
        return fail("请输入要润色的文本")

    style = data.get('style', 'formal')
    style_name = STYLE_MAP.get(style, '正式')

    prompt = POLISH_PROMPT.format(style=style_name)
    return _sse_response(prompt, text)


@tools_bp.route('/summarize', methods=['POST'])
@login_required
def summarize():
    """长文总结工具（SSE 流式）。"""
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()
    if not text:
        return fail("请输入要总结的文本")

    max_length = data.get('max_length', 'medium')
    length_val = LENGTH_MAP.get(max_length, 300)

    prompt = SUMMARIZE_PROMPT.format(max_length=length_val)
    # 截断过长文本，避免超出 token 限制
    truncated = text[:8000]
    return _sse_response(prompt, truncated)
