from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

pg_alchemy = SQLAlchemy()

# .env에서 DB 접속정보 읽어 Flask 앱에 SQLAlchemy 연결 (도커 내부 postgresql 호스트 사용)
def init_pg(app):
    db = os.getenv("POSTGRES_DB", "capstone_db")
    user = os.getenv("FLASK_DB_ID", "flask_server")
    pw = os.getenv("FLASK_DB_PW")
    host = "postgresql" # 도커에서만 작동

    #todo: env 파일 없을떄 예외처리 raise ValueError
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user}:{pw}@{host}:5432/{db}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    pg_alchemy.init_app(app)
