import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from flask_cors import CORS

temp_store = {}

def create_app():
    app = Flask(__name__)
    CORS(app)

    # 수정: 현재 파일(__init__.py)의 위치를 기준으로 절대 경로를 엶
    # 파일을 저장할 수 있도록 폴더를 세팅
    base_dir = os.path.abspath(os.path.dirname(__file__))
    # todo: 이미지 저장 경로 따로 생성했으니 테스트 바람

    media_base = os.getenv("MEDIA_STORAGE_BASE", "media")
    uploads_dir = os.getenv("MEDIA_STORAGE_UPLOADS", "uploads")
    results_dir = os.getenv("MEDIA_STORAGE_RESULTS", "results")
    save_dir = os.getenv("MEDIA_STORAGE_USERS", "users") # -> 영구 저장용

    temp_dir = os.getenv("MEDIA_STORAGE_TEMP", "temp")

    app.config['UPLOAD_FOLDER'] = os.path.join(media_base, uploads_dir)
    app.config['RESULT_FOLDER'] = os.path.join(media_base, results_dir)
    app.config['SAVE_FOLDER'] = os.path.join(media_base, save_dir) # -> 영구 저장용 새로 만든 폴더
    app.config['IMAGES_FOLDER'] = app.config['SAVE_FOLDER']
    app.config['TEMP_FOLDER'] = os.path.join(media_base, temp_dir)
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

    # 폴더가 없으면 미리 생성
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SAVE_FOLDER'], exist_ok=True) # -> 영구 저장용 새로 만든 폴더
    os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

    # 블루프린트들 불러오기
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.video import video_bp, analysis_bp
    from .routes.archive import archive_bp
    from .routes.media import media_bp

    # 메인 앱에 블루프린트 등록
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(archive_bp)
    app.register_blueprint(media_bp)

    return app