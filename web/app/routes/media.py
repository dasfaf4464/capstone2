"""
[ media 라우터 ]
사진 파일을 브라우저에 서빙하는 라우터

- GET /media/images/<filename>  → 사진 파일 서빙 (SAVE_FOLDER)
"""

from flask import Blueprint, send_from_directory, current_app

media_bp = Blueprint('media', __name__, url_prefix='/media')


@media_bp.route('/images/<filename>')
def serve_image(filename):
    # SAVE_FOLDER에서 사진 파일을 브라우저에 직접 서빙
    # 사진 파일 반환 (SAVE_FOLDER 기준)
    return send_from_directory(current_app.config['SAVE_FOLDER'], filename)
