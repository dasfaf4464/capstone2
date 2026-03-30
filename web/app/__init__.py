import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask

def create_app():
    app = Flask(__name__)

    # 수정: 현재 파일(__init__.py)의 위치를 기준으로 절대 경로를 엶
    # 파일을 저장할 수 있도록 폴더를 세팅
    base_dir = os.path.abspath(os.path.dirname(__file__))
    # todo: 이미지 저장 경로 따로 생성했으니 테스트 바람

    media_base = os.getenv("MEDIA_STORAGE_BASE", "media")
    uploads_dir = os.getenv("MEDIA_STORAGE_UPLOADS", "uploads")
    results_dir = os.getenv("MEDIA_STORAGE_RESULTS", "results")
    save_dir = os.getenv("MEDIA_STORAGE_USERS", "users") # -> 영구 저장용

    app.config['UPLOAD_FOLDER'] = os.path.join(media_base, uploads_dir)
    app.config['RESULT_FOLDER'] = os.path.join(media_base, results_dir)
    app.config['SAVE_FOLDER'] = os.path.join(media_base, save_dir) # -> 영구 저장용 새로 만든 폴더
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
    app.config['SECRET_KEY']          = os.getenv('SECRET_KEY', 'dev-secret-key')

    # 폴더가 없으면 미리 생성
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SAVE_FOLDER'], exist_ok=True) # -> 영구 저장용 새로 만든 폴더

    # PostgreSQL 초기화
    from .storage.core.pg import init_pg, pg_alchemy
    init_pg(app)

    # Flask-Login, Bcrypt 초기화
    from flask_login import LoginManager
    from flask_bcrypt import Bcrypt

    bcrypt       = Bcrypt(app)
    login_manager = LoginManager(app)

    # 6개 테이블들을 alchemy로 변환한 파일들이 있는 장소
    from .storage.alchemy_models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # Neo4j 제약조건 초기화
    from .storage.core.neo import init_neo4j_constraints
    try:
        init_neo4j_constraints()
    except Exception as e:
        print(f'[Neo4j] 초기화 실패 (무시): {e}')

    # 블루프린트들 불러오기
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.video import video_bp, analysis_bp
    from .routes.archive import archive_bp

    # 메인 앱에 블루프린트 등록
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(archive_bp)

    return app