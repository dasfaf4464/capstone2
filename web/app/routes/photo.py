"""
[ photo 라우터 ]
사진 업로드 / 분석 상태 조회 / 사진 목록 / 검색 API

- POST /api/photo/upload                     → 사진 업로드 + AI 분석 시작
- GET  /api/photo/status/<photo_uuid>        → 분석 진행 상태 조회
- GET  /api/travel/<travel_uuid>/photos      → 해당 여행 사진 목록
- GET  /api/photo/<photo_uuid>               → 사진 상세
- GET  /api/photo/search?keyword=            → 태그 키워드 검색
"""

import os
import uuid
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from ..storage.alchemy_models.photos import (
    save_photo, get_photos_by_travel, get_photo, search_photos_by_keyword
)
from ..ai.photo_analysis import run_photo_job, get_photo_job_status

photo_bp = Blueprint('photo', __name__, url_prefix='/api')


@photo_bp.route('/photo/upload', methods=['POST'])
def upload_photo():
    # 로그인 확인
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({'result': 'fail', 'msg': '로그인이 필요한 서비스입니다.'}), 401

    travel_uuid = request.form.get('travel_uuid')
    if not travel_uuid:
        return jsonify({'result': 'fail', 'msg': 'travel_uuid가 필요합니다.'}), 400

    files = request.files.getlist('photos')
    if not files:
        return jsonify({'result': 'fail', 'msg': '사진 파일이 없습니다.'}), 400

    uploaded = []
    save_folder = current_app.config['SAVE_FOLDER']

    for file in files:
        if not file or file.filename == '':
            continue

        # 파일명 보안 처리 + uuid 기반 새 이름
        ext         = os.path.splitext(secure_filename(file.filename))[1].lower()
        photo_uuid  = str(uuid.uuid4())
        filename    = f"{photo_uuid}{ext}"
        photo_path  = os.path.join(save_folder, filename)

        file.save(photo_path)

        try:
            # DB에 pending 상태로 저장
            photo = save_photo(
                travel_uuid=travel_uuid,
                user_uuid=user_uuid,
                photo_path=photo_path,
            )

            # 백그라운드 AI 분석 시작
            run_photo_job(
                photo_uuid=str(photo.photo_uuid),
                photo_path=photo_path,
                user_uuid=user_uuid,
                travel_uuid=travel_uuid,
                app=current_app._get_current_object(),
            )

            uploaded.append({
                'photo_uuid': str(photo.photo_uuid),
                'filename':   filename,
            })

        except Exception as e:
            return jsonify({'result': 'fail', 'msg': 'DB 저장 실패', 'details': str(e)}), 500

    return jsonify({
        'result':   'success',
        'msg':      f'{len(uploaded)}장 업로드 완료. AI 분석 중입니다.',
        'photos':   uploaded,
    }), 202


@photo_bp.route('/photo/status/<photo_uuid>', methods=['GET'])
def photo_status(photo_uuid):
    # AI 분석 상태 조회 (프론트가 폴링해서 씀)
    job = get_photo_job_status(photo_uuid)
    return jsonify({
        'result':     'success',
        'photo_uuid': photo_uuid,
        'status':     job.get('status'),
    }), 200


@photo_bp.route('/travel/<travel_uuid>/photos', methods=['GET'])
def travel_photos(travel_uuid):
    # 로그인 확인
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({'result': 'fail', 'msg': '로그인이 필요한 서비스입니다.'}), 401

    try:
        photos = get_photos_by_travel(travel_uuid)

        photos_data = [
            {
                'photo_uuid':      str(p.photo_uuid),
                'photo_path':      p.photo_path,
                'analysis_status': p.analysis_status,
                'main_category':   p.main_category,
                'sub_categories':  p.sub_categories or [],
                'has_person':      p.has_person,
                'activity':        p.activity,
            }
            for p in photos
        ]

        return jsonify({
            'result': 'success',
            'photos': photos_data,
        }), 200

    except Exception as e:
        return jsonify({'result': 'fail', 'msg': '사진 목록 조회 실패', 'details': str(e)}), 500


@photo_bp.route('/photo/<photo_uuid>', methods=['GET'])
def photo_detail(photo_uuid):
    # 로그인 확인
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({'result': 'fail', 'msg': '로그인이 필요한 서비스입니다.'}), 401

    photo = get_photo(photo_uuid)
    if not photo:
        return jsonify({'result': 'fail', 'msg': '사진을 찾을 수 없습니다.'}), 404

    return jsonify({
        'result': 'success',
        'photo': {
            'photo_uuid':      str(photo.photo_uuid),
            'photo_path':      photo.photo_path,
            'analysis_status': photo.analysis_status,
            'main_category':   photo.main_category,
            'sub_categories':  photo.sub_categories or [],
            'has_person':      photo.has_person,
            'activity':        photo.activity,
            'created_at':      photo.created_at.isoformat() if photo.created_at else None,
        }
    }), 200


@photo_bp.route('/photo/search', methods=['GET'])
def search_photos():
    # 로그인 확인
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({'result': 'fail', 'msg': '로그인이 필요한 서비스입니다.'}), 401

    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify({'result': 'fail', 'msg': 'keyword가 필요합니다.'}), 400

    try:
        photos = search_photos_by_keyword(user_uuid, keyword)

        photos_data = [
            {
                'photo_uuid':     str(p.photo_uuid),
                'photo_path':     p.photo_path,
                'main_category':  p.main_category,
                'sub_categories': p.sub_categories or [],
                'travel_uuid':    str(p.travel_uuid),
            }
            for p in photos
        ]

        return jsonify({
            'result':  'success',
            'keyword': keyword,
            'photos':  photos_data,
        }), 200

    except Exception as e:
        return jsonify({'result': 'fail', 'msg': '검색 실패', 'details': str(e)}), 500
