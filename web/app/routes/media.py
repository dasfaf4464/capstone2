"""
[ media 라우터 ]
사진 파일을 브라우저에 서빙하는 라우터

- GET /media/images/<filename>  → 사진 파일 서빙 (SAVE_FOLDER)
"""

from flask import Blueprint, send_from_directory, current_app

media_bp = Blueprint('media', __name__, url_prefix='/media')


@media_bp.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(current_app.config['SAVE_FOLDER'], filename)


@media_bp.route('/frames/<filename>')
def serve_frame(filename):
    return send_from_directory(current_app.config['RESULT_FOLDER'], filename)


@media_bp.route('/temp/<temp_id>')
def serve_temp(temp_id):
    entry = temp_store.get(temp_id)
    if not entry:
        return jsonify({'error': '유효하지 않거나 만료된 temp_id입니다.'}), 404
    return send_from_directory(current_app.config['TEMP_FOLDER'], entry['filename'])
