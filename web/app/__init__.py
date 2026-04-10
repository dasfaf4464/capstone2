import os
from flask import Flask
from flask_cors import CORS
# DB 매니저 불러오기
from .storage.core.pg import init_pg 

temp_store = {}

def create_app():
    app = Flask(__name__)
    CORS(app)

    init_pg(app)

    temp_dir = os.getenv("MEDIA_STORAGE_TEMP", "temp")

    app.config['UPLOAD_FOLDER'] = os.path.join(media_base, uploads_dir)
    app.config['RESULT_FOLDER'] = os.path.join(media_base, results_dir)
    app.config['SAVE_FOLDER'] = os.path.join(media_base, save_dir) # -> 영구 저장용 새로 만든 폴더
    app.config['IMAGES_FOLDER'] = app.config['SAVE_FOLDER']
    app.config['TEMP_FOLDER'] = os.path.join(media_base, temp_dir)
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SAVE_FOLDER'], exist_ok=True) # -> 영구 저장용 새로 만든 폴더
    os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

    # 블루프린트 등록
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.video import video_bp, analysis_bp
    from .routes.archive import archive_bp
    from .routes.media import media_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(archive_bp)
    app.register_blueprint(media_bp)

    return app