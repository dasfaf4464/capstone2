from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

# 1. 기본 주소 (http://localhost:5000/) 접속 시 로그인 화면 띄우기
@main_bp.route('/')
def index():
    return render_template('login.html')

# 2. 회원가입 화면 (http://localhost:5000/auth)
@main_bp.route('/auth')
def auth_page():
    return render_template('auth.html')

# 3. 영상 추출 메인 화면 (http://localhost:5000/extraction)
@main_bp.route('/extraction')
def extraction_page():
    return render_template('extraction.html')