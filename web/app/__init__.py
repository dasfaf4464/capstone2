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

    # 미디어 저장 폴더 설정
    media_base = os.getenv("MEDIA_STORAGE_BASE", "media")
    save_dir   = os.getenv("MEDIA_STORAGE_USERS", "users")

    app.config['SAVE_FOLDER'] = os.path.join(media_base, save_dir)
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

    os.makedirs(app.config['SAVE_FOLDER'], exist_ok=True)

    # 블루프린트 등록
    from .routes.main       import main_bp
    from .routes.auth       import auth_bp
    from .routes.travel     import travel_bp
    from .routes.photo      import photo_bp
    from .routes.user_stats import user_stats_bp
    from .routes.media      import media_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(travel_bp)
    app.register_blueprint(photo_bp)
    app.register_blueprint(user_stats_bp)
    app.register_blueprint(media_bp)

    return app
