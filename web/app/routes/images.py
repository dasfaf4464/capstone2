"""
[ images 라우터 ]
분석 결과 이미지 저장 / 아카이브 조회 / 다운로드 API 담당함
모든 DB 처리는 storage/alchemy_models/images.py 의 함수 씀

- POST /api/image/save                   → 분석된 이미지 아카이브에 저장
- GET  /api/image/list                   → 내 아카이브 전체 목록 조회
- GET  /api/image/download/<image_uuid>  → 이미지 파일 다운로드

※ update_tag, search_archive 는 DB API 준비되면 추가 예정
"""

from flask import Blueprint, request, jsonify, current_app, send_file, session
import os
from ..storage.alchemy_models.images import save_image as db_save_image, get_images_by_user

images_bp = Blueprint('images', __name__, url_prefix='/api/image')


@images_bp.route('/save', methods=['POST'])
def save_image():
    # 로그인 확인
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({"result": "fail", "msg": "로그인이 필요한 서비스입니다."}), 401

    # 요청 body 에서 image_path, image_query 꺼냄
    data = request.json or {}
    image_path = data.get('image_path')
    image_query = data.get('image_query')  # 분석 시 입력했던 쿼리 텍스트

    if not image_path or not image_query:
        return jsonify({"result": "fail", "msg": "image_path와 image_query가 필요합니다."}), 400

    try:
        # DB에 이미지 저장
        image = db_save_image(image_path=image_path, user_uuid=user_uuid, image_query=image_query)
        if not image:
            return jsonify({"result": "fail", "msg": "이미지 저장 실패"}), 500

        return jsonify({
            "result": "success",
            "msg": "이미지 저장 완료",
            "image_data": {
                "image_uuid":  str(image.image_uuid),
                "image_path":  image.image_path,
                "image_query": image.image_query,
            }
        }), 201

    except Exception as e:
        return jsonify({"result": "fail", "msg": "이미지 저장 실패", "details": str(e)}), 500


@images_bp.route('/list', methods=['GET'])
def get_archive_list():
    # 로그인 확인
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({"result": "fail", "msg": "로그인이 필요한 서비스입니다."}), 401

    try:
        # 해당 유저의 이미지 전체 조회
        images = get_images_by_user(user_uuid)

        # ORM 객체를 dict 로 변환해서 응답
        images_list = [
            {
                "image_uuid":        str(img.image_uuid),
                "image_path":        img.image_path,
                "image_query":       img.image_query,
                "tag":               img.image_description,  # 태그는 image_description 컬럼 씀
                "image_create_time": img.image_create_time.isoformat() if img.image_create_time else None,
            }
            for img in images
        ]

        return jsonify({
            "result": "success",
            "msg": "아카이브 목록 조회 성공",
            "images_list": images_list
        }), 200

    except Exception as e:
        return jsonify({"result": "fail", "msg": "목록 조회 실패", "details": str(e)}), 500


@images_bp.route('/download/<image_uuid>', methods=['GET'])
def download_image(image_uuid):
    # RESULT_FOLDER 에서 {image_uuid}.jpg 파일 찾아서 전송
    result_folder = current_app.config['RESULT_FOLDER']
    file_path = os.path.join(result_folder, f"{image_uuid}.jpg")

    if not os.path.exists(file_path):
        return jsonify({"result": "fail", "msg": "파일을 찾을 수 없습니다."}), 404

    return send_file(
        file_path,
        mimetype='image/jpeg',
        as_attachment=True,
        download_name=f"{image_uuid}.jpg"
    )
