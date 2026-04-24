"""
[ travel 라우터 ]
여행 생성 / 목록 조회 API

- POST /api/travel/create  → 여행 생성 (이름 + 기간 사용자 입력)
- GET  /api/travel/list    → 내 여행 목록 조회
"""

from flask import Blueprint, request, jsonify, session
from ..storage.alchemy_models.travels import create_travel, get_travels_by_user

travel_bp = Blueprint('travel', __name__, url_prefix='/api/travel')


@travel_bp.route('/create', methods=['POST'])
def create():
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
