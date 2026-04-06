import os
from flask import Flask
from flask_cors import CORS
# DB 매니저 불러오기
from .storage.core.pg import init_pg 

def create_app():
    app = Flask(__name__)
    CORS(app)

    init_pg(app)

    # .env 파일의 환경 변수를 읽어와서 동적으로 경로 설정
    storage_base = os.environ.get('MEDIA_STORAGE_BASE', '/media')
    upload_folder_name = os.environ.get('MEDIA_STORAGE_UPLOADS', 'uploads')
    result_folder_name = os.environ.get('MEDIA_STORAGE_RESULTS', 'results')
    
    # 최종 물리 경로 조합 (예: /media/uploads)
    app.config['UPLOAD_FOLDER'] = os.path.join(storage_base, upload_folder_name)
    app.config['RESULT_FOLDER'] = os.path.join(storage_base, result_folder_name)
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

    # 블루프린트 등록
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.video import video_bp
    from .routes.image import image_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(image_bp)

    return app