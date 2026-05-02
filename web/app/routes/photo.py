"""
[ photo 라우터 ]
사진 업로드 / 분석 상태 조회 / 사진 목록 / 검색 API

- POST /api/photo/upload                     → 사진 업로드 + AI 분석 시작
- GET  /api/photo/status/<photo_uuid>        → 분석 진행 상태 조회
- POST /api/photo/<photo_uuid>/retry         → 실패 사진 AI 분석 재시도
- GET  /api/travel/<travel_uuid>/photos      → 해당 여행 사진 목록
- GET  /api/travel/<travel_uuid>/stats       → 해당 여행 카테고리·키워드 통계
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
from ..storage.alchemy_models.travels import get_travel
from ..ai.photo_analysis import run_photo_job, get_photo_job_status

photo_bp = Blueprint('photo', __name__, url_prefix='/api')


@photo_bp.route('/photo/upload', methods=['POST'])
def upload_photo():
    # 사진 파일 저장 + DB pending 등록 + 백그라운드 AI 분석 시작, 즉시 202 반환
    # 로그인 확인
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({'result': 'fail', 'msg': '로그인이 필요한 서비스입니다.'}), 401

    travel_uuid = request.form.get('travel_uuid')
    if not travel_uuid:
        return jsonify({'result': 'fail', 'msg': 'travel_uuid가 필요합니다.'}), 400

    # travel 소유권 확인 (다른 유저의 travel에 업로드 차단)
    travel = get_travel(travel_uuid)
    if not travel or str(travel.user_uuid) != str(user_uuid):
        return jsonify({'result': 'fail', 'msg': '해당 여행에 접근할 수 없습니다.'}), 403

    files = request.files.getlist('photos')
    if not files:
        return jsonify({'result': 'fail', 'msg': '사진 파일이 없습니다.'}), 400

    uploaded = []
    failed   = []
    save_folder = current_app.config['SAVE_FOLDER']

    for file in files:
        if not file or file.filename == '':
            continue

        # 파일명 보안 처리 + uuid 기반 새 이름
        ext        = os.path.splitext(secure_filename(file.filename))[1].lower()
        filename   = f"{uuid.uuid4()}{ext}"
        photo_path = os.path.join(save_folder, filename)

        try:
            file.save(photo_path)

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
            # 실패한 사진은 디스크에서 제거 후 다음 사진 계속 진행
            if os.path.exists(photo_path):
                os.remove(photo_path)
            failed.append({'filename': file.filename, 'reason': str(e)})

    if not uploaded:
        return jsonify({'result': 'fail', 'msg': '모든 사진 업로드 실패', 'failed': failed}), 500

    return jsonify({
        'result':   'success',
        'msg':      f'{len(uploaded)}장 업로드 완료. AI 분석 중입니다.',
        'photos':   uploaded,
        'failed':   failed,  # 일부 실패 시 어떤 파일인지 프론트에 전달
    }), 202


@photo_bp.route('/photo/status/<photo_uuid>', methods=['GET'])
def photo_status(photo_uuid):
    # 특정 사진의 AI 분석 진행 상태 반환 (프론트가 폴링해서 done/fail 확인)
    # AI 분석 상태 조회 (프론트가 폴링해서 씀)
    job = get_photo_job_status(photo_uuid)
    return jsonify({
        'result':     'success',
        'photo_uuid': photo_uuid,
        'status':     job.get('status'),
    }), 200


@photo_bp.route('/photo/<photo_uuid>/retry', methods=['POST'])
def retry_photo(photo_uuid):
    # 분석 실패 사진을 pending으로 초기화하고 AI 분석 재시도 (본인 사진만 허용)
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({'result': 'fail', 'msg': '로그인이 필요한 서비스입니다.'}), 401

    photo = get_photo(photo_uuid)
    if not photo or str(photo.user_uuid) != str(user_uuid):
        return jsonify({'result': 'fail', 'msg': '사진을 찾을 수 없습니다.'}), 404

    if photo.analysis_status != 'fail':
        return jsonify({'result': 'fail', 'msg': '실패 상태의 사진만 재시도할 수 있습니다.'}), 400

    try:
        from ..storage.alchemy_models.photos import reset_to_pending

        reset_to_pending(photo_uuid)

        run_photo_job(
            photo_uuid=str(photo.photo_uuid),
            photo_path=photo.photo_path,
            user_uuid=user_uuid,
            travel_uuid=str(photo.travel_uuid),
            app=current_app._get_current_object(),
        )

        return jsonify({'result': 'success', 'msg': '분석을 다시 시작합니다.'}), 202

    except Exception as e:
        return jsonify({'result': 'fail', 'msg': '재시도 실패', 'details': str(e)}), 500


@photo_bp.route('/travel/<travel_uuid>/photos', methods=['GET'])
def travel_photos(travel_uuid):
    # 특정 여행에 속한 사진 목록 전체 반환 (AI 분석 결과 포함)
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


@photo_bp.route('/photo/search', methods=['GET'])
def search_photos():
    # ?keyword= 파라미터로 sub_categories JSONB 검색해 해당 사진 목록 반환
    # 로그인 확인
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({'result': 'fail', 'msg': '로그인이 필요한 서비스입니다.'}), 401

    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify({'result': 'fail', 'msg': 'keyword가 필요합니다.'}), 400

    try:
        # search_photos_by_keyword가 이미 dict 리스트 반환
        photos_data = search_photos_by_keyword(user_uuid, keyword)

        return jsonify({
            'result':  'success',
            'keyword': keyword,
            'photos':  photos_data,
        }), 200

    except Exception as e:
        return jsonify({'result': 'fail', 'msg': '검색 실패', 'details': str(e)}), 500


@photo_bp.route('/photo/<photo_uuid>', methods=['GET'])
def photo_detail(photo_uuid):
    # 사진 1장 상세 정보 반환 (카테고리·키워드·인물·활동 등 분석 결과 포함)
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


@photo_bp.route('/travel/<travel_uuid>/stats', methods=['GET'])
def travel_stats(travel_uuid):
    # 특정 여행의 카테고리 비율·키워드 빈도 통계 반환 (여행 상세 화면 차트용)
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({'result': 'fail', 'msg': '로그인이 필요한 서비스입니다.'}), 401

    travel = get_travel(travel_uuid)
    if not travel or str(travel.user_uuid) != str(user_uuid):
        return jsonify({'result': 'fail', 'msg': '해당 여행에 접근할 수 없습니다.'}), 403

    try:
        from ..storage.alchemy_models.photos import (
            get_travel_category_stats, get_travel_keyword_stats,
            get_travel_person_stats, get_travel_activity_stats,
        )

        category_stats = get_travel_category_stats(travel_uuid)
        keyword_stats  = get_travel_keyword_stats(travel_uuid)
        person_stats   = get_travel_person_stats(travel_uuid)
        activity_stats = get_travel_activity_stats(travel_uuid)

        return jsonify({
            'result':         'success',
            'travel_name':    travel.travel_name,
            'category_stats': category_stats,
            'keyword_stats':  keyword_stats,
            'person_stats':   person_stats,
            'activity_stats': activity_stats,
        }), 200

    except Exception as e:
        return jsonify({'result': 'fail', 'msg': '통계 조회 실패', 'details': str(e)}), 500
