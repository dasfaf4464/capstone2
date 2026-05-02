"""
[ travel 라우터 ]
여행 생성 / 목록 조회 / 삭제 API

- POST   /api/travel/create          → 여행 생성 (이름 + 기간 사용자 입력)
- GET    /api/travel/list            → 내 여행 목록 조회
- DELETE /api/travel/<travel_uuid>   → 여행 + 관련 사진(DB + 디스크) 전체 삭제
"""

import os
import threading
from flask import Blueprint, request, jsonify, session, current_app
from ..storage.alchemy_models.travels import create_travel, get_travels_by_user, get_travel, delete_travel
from ..storage.alchemy_models.photos import get_photos_by_travel

travel_bp = Blueprint('travel', __name__, url_prefix='/api/travel')


@travel_bp.route('/create', methods=['POST'])
def create():
    # 여행 이름·시작일·종료일 받아 travels 테이블에 새 여행 생성
    # 로그인 확인
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({'result': 'fail', 'msg': '로그인이 필요한 서비스입니다.'}), 401

    data        = request.json or {}
    travel_name = data.get('travel_name')
    start_date  = data.get('start_date')
    end_date    = data.get('end_date')

    if not all([travel_name, start_date, end_date]):
        return jsonify({'result': 'fail', 'msg': 'travel_name, start_date, end_date가 필요합니다.'}), 400

    try:
        travel = create_travel(
            user_uuid=user_uuid,
            travel_name=travel_name,
            start_date=start_date,
            end_date=end_date,
        )
        return jsonify({
            'result': 'success',
            'msg': '여행 생성 완료',
            'travel_data': {
                'travel_uuid': str(travel.travel_uuid),
                'travel_name': travel.travel_name,
                'start_date':  str(travel.start_date),
                'end_date':    str(travel.end_date),
            }
        }), 201

    except Exception as e:
        return jsonify({'result': 'fail', 'msg': '여행 생성 실패', 'details': str(e)}), 500


@travel_bp.route('/list', methods=['GET'])
def travel_list():
    # 현재 로그인 유저의 여행 목록 전체 반환 (최신순)
    # 로그인 확인
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({'result': 'fail', 'msg': '로그인이 필요한 서비스입니다.'}), 401

    try:
        travels = get_travels_by_user(user_uuid)

        travels_data = [
            {
                'travel_uuid':      str(t.travel_uuid),
                'travel_name':      t.travel_name,
                'start_date':       str(t.start_date),
                'end_date':         str(t.end_date),
                'cover_photo_path': t.cover_photo_path,
            }
            for t in travels
        ]

        return jsonify({
            'result':  'success',
            'travels': travels_data,
        }), 200

    except Exception as e:
        return jsonify({'result': 'fail', 'msg': '목록 조회 실패', 'details': str(e)}), 500


@travel_bp.route('/<travel_uuid>', methods=['DELETE'])
def delete(travel_uuid):
    # 여행 삭제: 해당 여행의 사진 파일(디스크) 먼저 제거 후 DB 레코드 삭제 (CASCADE)
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({'result': 'fail', 'msg': '로그인이 필요한 서비스입니다.'}), 401

    travel = get_travel(travel_uuid)
    if not travel or str(travel.user_uuid) != str(user_uuid):
        return jsonify({'result': 'fail', 'msg': '해당 여행을 찾을 수 없습니다.'}), 404

    try:
        # 1) 사진 파일 목록 수집 후 디스크에서 삭제
        photos = get_photos_by_travel(travel_uuid)
        deleted_files, failed_files = 0, 0
        for photo in photos:
            try:
                if photo.photo_path and os.path.exists(photo.photo_path):
                    os.remove(photo.photo_path)
                    deleted_files += 1
            except Exception:
                failed_files += 1  # 파일 삭제 실패해도 DB 삭제는 계속 진행

        # 2) DB 삭제 (travels 삭제 → photos CASCADE 삭제)
        delete_travel(travel_uuid)

        # 3) 백그라운드에서 유저 통계 재집계 (사진 없으면 NULL, 있으면 LLM 재생성)
        app = current_app._get_current_object()
        def _refresh():
            with app.app_context():
                try:
                    from ..ai.photo_analysis import _refresh_user_stats
                    _refresh_user_stats(user_uuid)
                except Exception as e:
                    print(f"[travel delete] 통계 갱신 실패: {e}")
        threading.Thread(target=_refresh, daemon=True).start()

        return jsonify({
            'result':        'success',
            'msg':           '여행이 삭제되었습니다.',
            'deleted_files': deleted_files,
            'failed_files':  failed_files,
        }), 200

    except Exception as e:
        return jsonify({'result': 'fail', 'msg': '삭제 실패', 'details': str(e)}), 500
