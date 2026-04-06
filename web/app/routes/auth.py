from flask import Blueprint, request, jsonify, session
from sqlalchemy import text
from ..storage.core.pg import pg_alchemy as db # 데이터베이스 통신을 위한 객체

# '/api/auth'로 시작하는 모든 요청을 이 블루프린트가 처리하도록 설정
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# 회원가입 API (/api/auth/signup)
@auth_bp.route('/signup', methods=['POST'])
def signup():
    # 프론트엔드에서 보낸 JSON 데이터를 받아옴
    data = request.json or {}
    
    # API 명세서에 정의된 변수명(id, pw)으로 데이터를 추출
    user_id = data.get('id')
    user_pw = data.get('pw')
    user_email = data.get('email')
    
    # id나 pw 중 하나라도 안 보냈다면 에러를 반환
    if not user_id or not user_pw or not user_email:
        return jsonify({"result": "fail", "msg": "id와 pw, email을 모두 입력해주세요."}), 400

    try:
        # DB의 users 테이블에 데이터를 넣는 SQL 쿼리문
        query = text("""
            INSERT INTO users (user_nickname, user_pw, user_email) 
            VALUES (:id, :pw, :email) 
            RETURNING user_uuid
        """)
        
        # 쿼리를 실행하고 결과를 받아옴
        result = db.session.execute(query, {"id": user_id, "pw": user_pw, "email": user_email})
        
        # 새롭게 생성된 유저의 고유 식별자(user_uuid)를 가져옴
        new_user_uuid = str(result.fetchone()[0])
        
        # 데이터베이스에 변경 사항을 최종적으로 저장
        db.session.commit()
        
        # 성공 메시지와 함께 새로 발급된 user_uuid를 프론트엔드로 보냄
        return jsonify({"result": "success", "msg": "회원가입이 완료되었습니다.", "user_uuid": new_user_uuid}), 201
        
    except Exception as e:
        # 에러가 발생하면 DB 저장 내역을 되돌림
        db.session.rollback()
        # id(닉네임)가 중복되었거나 다른 DB 에러가 났을 때 실패 응답을 보냄
        return jsonify({"result": "fail", "msg": "회원가입 실패 (아이디 중복 등)", "details": str(e)}), 500


# 로그인 API (/api/auth/login)
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    user_id = data.get('id')
    user_pw = data.get('pw')
    
    # 입력받은 id(user_nickname)와 pw가 일치하는 유저의 고유 식별자를 찾는 쿼리
    query = text("SELECT user_uuid FROM users WHERE user_nickname = :id AND user_pw = :pw")
    result = db.session.execute(query, {"id": user_id, "pw": user_pw}).fetchone()
    
    # DB에서 검색된 결과가 있다면 (로그인 성공)
    if result:
        # 세션(서버 메모리)에 해당 유저의 고유번호를 저장하여 '로그인 상태'를 유지
        session['user_uuid'] = str(result[0])
        return jsonify({"result": "success", "msg": "로그인 성공"}), 200
    else:
        # 결과가 없다면 아이디나 비밀번호가 틀린 것
        return jsonify({"result": "fail", "msg": "아이디 또는 비밀번호가 틀렸습니다."}), 401


# 로그아웃 API (/api/auth/logout)
@auth_bp.route('/logout', methods=['POST'])
def logout():
    # 현재 유지되고 있는 세션에서 'user_uuid'를 삭제하여 로그아웃 처리
    session.pop('user_uuid', None)
    return jsonify({"result": "success", "msg": "로그아웃 되었습니다."}), 200