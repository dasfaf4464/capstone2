"""
[ auth 라우터 ]
회원가입 / 로그인 / 로그아웃 API 담당함
모든 DB 처리는 storage/alchemy_models/user.py 의 함수 씀

- POST /api/auth/signup  → 회원가입
- POST /api/auth/login   → 로그인 (세션에 user_uuid 저장함)
- POST /api/auth/logout  → 로그아웃 (세션 삭제)
"""

from flask import Blueprint, request, jsonify, session
from ..storage.alchemy_models.user import signup as db_signup, login as db_login

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/signup', methods=['POST'])
def signup():
    # ID/PW 받아 유저 생성, 중복 ID면 400 반환
    # 요청 body 에서 id, pw 꺼냄
    data = request.json or {}
    user_id = data.get('id')
    user_pw = data.get('pw')

    # id 또는 pw 없으면 400 반환
    if not user_id or not user_pw:
        return jsonify({"result": "fail", "msg": "id와 pw를 모두 입력해주세요."}), 400

    try:
        # db_signup 성공 시 User 객체 반환, 중복 id면 None 반환
        new_user = db_signup(user_id, user_pw)

        if new_user:
            # 가입 성공 → user_uuid, user_id 같이 응답
            return jsonify({
                "result": "success",
                "msg": "회원가입이 완료되었습니다.",
                "user_data": {
                    "user_uuid": str(new_user.user_uuid),
                    "user_id": new_user.user_id
                }
            }), 201
        else:
            # 이미 존재하는 id
            return jsonify({"result": "fail", "msg": "이미 존재하는 아이디입니다."}), 400

    except Exception as e:
        return jsonify({"result": "fail", "msg": "회원가입 실패", "details": str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    # ID/PW 검증 후 성공 시 session에 user_uuid 저장
    # 요청 body 에서 id, pw 꺼냄
    data = request.json or {}
    user_id = data.get('id')
    user_pw = data.get('pw')

    try:
        # db_login 성공 시 User 객체 반환, 실패 시 None 반환
        user = db_login(user_id, user_pw)

        if user:
            # 로그인 성공 → 세션에 user_uuid 저장 (이후 API 인증에 씀)
            session['user_uuid'] = str(user.user_uuid)

            return jsonify({
                "result": "success",
                "msg": "로그인 성공",
                "user_data": {
                    "user_uuid": str(user.user_uuid),
                    "user_id": user.user_id
                }
            }), 200
        else:
            # id 또는 pw 틀림
            return jsonify({"result": "fail", "msg": "아이디 또는 비밀번호가 틀렸습니다."}), 401

    except Exception as e:
        return jsonify({"result": "fail", "msg": "로그인 처리 중 에러 발생", "details": str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    # session에서 user_uuid 제거해 로그아웃 처리
    # 세션에서 user_uuid 제거하면 로그아웃 됨
    session.pop('user_uuid', None)
    return jsonify({"result": "success", "msg": "로그아웃 되었습니다."}), 200
