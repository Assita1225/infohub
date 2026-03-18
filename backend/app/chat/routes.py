"""Chat 模块路由 —— 4 个端点，POST /message 支持 SSE 流式响应。"""

import json
import logging

from flask import request, Response, stream_with_context

from . import chat_bp
from .services import (
    create_session, list_sessions, get_session,
    delete_session, add_message, build_prompt,
)
from ..common.auth import login_required
from ..common.response import success, fail
from ..common.llm_client import llm_client

logger = logging.getLogger(__name__)


@chat_bp.route('/message', methods=['POST'])
@login_required
def send_message():
    """发送消息并获取 AI 流式回复（SSE）。"""
    data = request.get_json(silent=True) or {}
    content = data.get('content', '').strip()
    if not content:
        return fail("消息内容不能为空")

    session_id = data.get('session_id')
    context = data.get('context')

    # 无 session_id 时自动创建会话
    if not session_id:
        session = create_session(context)
        session_id = session['_id']
    else:
        # 验证会话存在
        if not get_session(session_id):
            return fail("会话不存在", 404)

    # 保存用户消息
    add_message(session_id, 'user', content)

    # 构建 prompt
    system_prompt, messages = build_prompt(session_id, content)

    def generate():
        full_response = []
        try:
            for chunk in llm_client.chat(messages, system_prompt=system_prompt, stream=True):
                full_response.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk, 'session_id': session_id}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error("Chat SSE stream error: %s", e)
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        else:
            # 流正常结束 → 保存 assistant 完整回复
            add_message(session_id, 'assistant', ''.join(full_response))
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


@chat_bp.route('/sessions', methods=['GET'])
@login_required
def get_sessions():
    """获取会话列表。"""
    sessions = list_sessions()
    return success(sessions)


@chat_bp.route('/sessions/<session_id>', methods=['GET'])
@login_required
def get_session_detail(session_id):
    """获取会话详情（含完整消息历史）。"""
    session = get_session(session_id)
    if not session:
        return fail("会话不存在", 404)
    return success(session)


@chat_bp.route('/sessions/<session_id>', methods=['DELETE'])
@login_required
def remove_session(session_id):
    """删除会话。"""
    if not delete_session(session_id):
        return fail("会话不存在", 404)
    return success(message="会话已删除")
