import os
from flask import Flask
from flask_cors import CORS
from .storage.core.pg import init_pg


# Flask 앱 생성, DB 연결, Blueprint 6개 등록, 미디어 저장 폴더 초기화
def create_app():
    app = Flask(__name__)
    CORS(app)

    app.secret_key = "yolo_team_super_secret_key"

    init_pg(app)

    temp_dir = os.getenv("MEDIA_STORAGE_TEMP", "temp")
    media_base = os.getenv("MEDIA_STORAGE_BASE", "media")
    uploads_dir = os.getenv("MEDIA_STORAGE_UPLOADS", "uploads")
    results_dir = os.getenv("MEDIA_STORAGE_RESULTS", "results")
    save_dir = os.getenv("MEDIA_STORAGE_USERS", "users")

    app.config['UPLOAD_FOLDER'] = os.path.join(media_base, uploads_dir)
    app.config['RESULT_FOLDER'] = os.path.join(media_base, results_dir)
    app.config['SAVE_FOLDER'] = os.path.join(media_base, save_dir)
    app.config['TEMP_FOLDER'] = os.path.join(media_base, temp_dir)
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SAVE_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

    # 블루프린트 등록
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.video import video_bp
    from .routes.images import image_bp
    from .routes.media import media_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(media_bp)

    return app
