"""
[ media 라우터 ]
파일을 직접 브라우저에 서빙하는 라우터임
DB 없이 파일 경로만으로 이미지/영상 반환함

- GET /media/images/<filename>  → 영구 저장된 이미지 서빙 (SAVE_FOLDER)
- GET /media/frames/<filename>  → AI 분석 결과 top5 프레임 서빙 (RESULT_FOLDER, 임시)
- GET /media/temp/<temp_id>     → 업로드 후 confirm 전 임시 이미지 미리보기 (TEMP_FOLDER)
"""

from flask import Blueprint, send_from_directory, jsonify, current_app
from .. import temp_store

media_bp = Blueprint('media', __name__, url_prefix='/media')


@media_bp.route('/images/<filename>')
def serve_image(filename):
    # 영구 저장된 유저 이미지 반환 (SAVE_FOLDER 기준)
    return send_from_directory(current_app.config['SAVE_FOLDER'], filename)


@media_bp.route('/frames/<filename>')
def serve_frame(filename):
    # AI 분석 완료 후 생성된 top5 프레임 반환 (RESULT_FOLDER 기준)
    # 파일명 형식: {video_uuid}_top1.jpg ~ top5.jpg
    return send_from_directory(current_app.config['RESULT_FOLDER'], filename)


@media_bp.route('/temp/<temp_id>')
def serve_temp(temp_id):
    # 업로드 직후 confirm 전 임시 미리보기용
    # temp_store 는 app/__init__.py 에 선언된 메모리 딕셔너리임
    entry = temp_store.get(temp_id)
    if not entry:
        return jsonify({'error': '유효하지 않거나 만료된 temp_id입니다.'}), 404
    return send_from_directory(current_app.config['TEMP_FOLDER'], entry['filename'])
