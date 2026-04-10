"""
미디어 파일 서빙 라우트.

GET /media/images/<filename>   — 영구 이미지
GET /media/frames/<filename>   — 파이프라인 top5 프레임 (임시)
GET /media/temp/<temp_id>      — confirm 전 임시 이미지 미리보기
"""

from flask import Blueprint, send_from_directory, jsonify, current_app
from .. import temp_store

media_bp = Blueprint('media', __name__, url_prefix='/media')


@media_bp.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(current_app.config['IMAGES_FOLDER'], filename)


@media_bp.route('/frames/<filename>')
def serve_frame(filename):
    return send_from_directory(current_app.config['RESULT_FOLDER'], filename)


@media_bp.route('/temp/<temp_id>')
def serve_temp(temp_id):
    entry = temp_store.get(temp_id)
    if not entry:
        return jsonify({'error': '유효하지 않거나 만료된 temp_id입니다.'}), 404
    return send_from_directory(current_app.config['TEMP_FOLDER'], entry['filename'])
