"""
[ main 라우터 ]
HTML 페이지 서빙 담당

- GET /         → 로그인 페이지
- GET /signup   → 회원가입 페이지
- GET /home     → 메인화면 (성향 요약)
- GET /archive  → 아카이브 (여행 목록)
- GET /travel/<travel_uuid> → 여행 세부 (3x3 그리드)
- GET /search   → 태그 검색
- GET /upload   → 사진 업로드
- GET /analysis → 성향 분석
"""

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('login.html')


@main_bp.route('/signup')
def signup_page():
    return render_template('auth.html')


@main_bp.route('/home')
def home():
    return render_template('index.html')


@main_bp.route('/archive')
def archive():
    return render_template('archive.html')


@main_bp.route('/travel/<travel_uuid>')
def travel_detail(travel_uuid):
    return render_template('travel_detail.html', travel_uuid=travel_uuid)


@main_bp.route('/search')
def search():
    return render_template('search.html')


@main_bp.route('/upload')
def upload():
    return render_template('upload.html')


@main_bp.route('/analysis')
def analysis():
    return render_template('analysis.html')
