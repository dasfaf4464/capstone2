from flask import Blueprint, request, jsonify
import uuid

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    # 데이터 정의서: email, nickname, password 입력 받음
    data = request.json
    
    # TODO: 회원가입 로직 및 DB/스토리지 할당 로직 작성
    # user_id는 고유 UUID로 생성
    new_user_id = str(uuid.uuid4())
    
    return jsonify({
        "message": "회원가입이 완료되었습니다.",
        "user_id": new_user_id
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    # TODO: 세션 기반 로그인 처리 및 상태 유지 로직
    
    return jsonify({"message": "로그인 성공"}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    # TODO: 세션 파기 등 로그아웃 처리 로직
    
    return jsonify({"message": "로그아웃 되었습니다."}), 200