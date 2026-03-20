from flask import request, send_file

from app.common.auth import login_required
from app.common.response import success, fail, paginated
from . import notes_bp
from .services import (
    create_note, list_notes, get_note, update_note,
    soft_delete_note, restore_note, search_notes, list_trash,
    export_note_md, export_notes_batch,
)


# ── 列表 & 创建 ──

@notes_bp.route('/', methods=['GET'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    search = request.args.get('search')
    tag = request.args.get('tag')
    sort = request.args.get('sort', 'updated_at')
    items, total = list_notes(page, page_size, search, tag, sort)
    return paginated(items, total, page, page_size)


@notes_bp.route('/', methods=['POST'])
@login_required
def create():
    data = request.get_json(silent=True) or {}
    if not data.get('title', '').strip():
        return fail("标题不能为空")
    note = create_note(data)
    return success(note, "创建成功")


# ── 搜索 & 回收站（静态路径，必须在 /<note_id> 之前）──

@notes_bp.route('/search', methods=['GET'])
@login_required
def search():
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    items, total = search_notes(q, page, page_size)
    return paginated(items, total, page, page_size)


@notes_bp.route('/export-batch', methods=['POST'])
@login_required
def batch_export():
    """批量导出笔记为 zip"""
    data = request.get_json(silent=True) or {}
    ids = data.get('ids', [])
    if not ids:
        return fail("请选择要导出的笔记")
    buf = export_notes_batch(ids)
    return send_file(buf, mimetype='application/zip',
                     as_attachment=True, download_name='notes_export.zip')


@notes_bp.route('/trash', methods=['GET'])
@login_required
def trash():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    items, total = list_trash(page, page_size)
    return paginated(items, total, page, page_size)


# ── 单条操作（动态路径）──

@notes_bp.route('/<note_id>', methods=['GET'])
@login_required
def detail(note_id):
    note = get_note(note_id)
    if not note:
        return fail("笔记不存在", 404)
    return success(note)


@notes_bp.route('/<note_id>', methods=['PUT'])
@login_required
def update(note_id):
    data = request.get_json(silent=True) or {}
    note = update_note(note_id, data)
    if not note:
        return fail("笔记不存在", 404)
    return success(note, "更新成功")


@notes_bp.route('/<note_id>', methods=['DELETE'])
@login_required
def delete(note_id):
    if not soft_delete_note(note_id):
        return fail("笔记不存在", 404)
    return success(None, "已移入回收站")


@notes_bp.route('/<note_id>/restore', methods=['POST'])
@login_required
def do_restore(note_id):
    if not restore_note(note_id):
        return fail("笔记不存在或未删除", 404)
    return success(None, "已恢复")


@notes_bp.route('/<note_id>/export', methods=['GET'])
@login_required
def export_single(note_id):
    """导出单篇笔记为 Markdown"""
    import io
    filename, content = export_note_md(note_id)
    if filename is None:
        return fail("笔记不存在", 404)
    buf = io.BytesIO(content.encode('utf-8'))
    return send_file(buf, mimetype='text/markdown',
                     as_attachment=True, download_name=filename)
