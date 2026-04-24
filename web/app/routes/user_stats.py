"""
[ user_stats 라우터 ]
사용자 통계 + 성향 분석 + 추천 API

- GET /api/user/stats          → 카테고리 통계 + 키워드 상위 10개
- GET /api/user/recommendation → 성향 문구 + 추천 글
"""

from flask import Blueprint, jsonify, session
from ..storage.alchemy_models.user_stats import get_user_stats

user_stats_bp = Blueprint('user_stats', __name__, url_prefix='/api/user')


@user_stats_bp.route('/stats', methods=['GET'])
def get_stats():
    # 로그인 확인
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({'result': 'fail', 'msg': '로그인이 필요한 서비스입니다.'}), 401

    try:
        stats = get_user_stats(user_uuid)

        if not stats:
            # 아직 업로드한 사진 없음
            return jsonify({
                'result':         'success',
                'category_stats': {},
                'keyword_stats':  [],
            }), 200

        return jsonify({
            'result':         'success',
            'category_stats': stats.category_stats or {},
            'keyword_stats':  stats.keyword_stats  or [],
        }), 200

    except Exception as e:
        return jsonify({'result': 'fail', 'msg': '통계 조회 실패', 'details': str(e)}), 500


@user_stats_bp.route('/recommendation', methods=['GET'])
def get_recommendation():
    # 로그인 확인
    user_uuid = session.get('user_uuid')
    if not user_uuid:
        return jsonify({'result': 'fail', 'msg': '로그인이 필요한 서비스입니다.'}), 401

    try:
        stats = get_user_stats(user_uuid)

        if not stats or not stats.personality_type:
            return jsonify({
                'result':          'success',
                'personality_type': '여행 사진을 올리면 성향을 분석해드립니다!',
                'recommendation':   '사진을 업로드하고 나만의 여행 성향을 확인해보세요.',
            }), 200

        return jsonify({
            'result':           'success',
            'personality_type': stats.personality_type,
            'recommendation':   stats.recommendation,
        }), 200

    except Exception as e:
        return jsonify({'result': 'fail', 'msg': '추천 조회 실패', 'details': str(e)}), 500
