from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

pg_alchemy = SQLAlchemy()

def init_pg(app):
    db = os.getenv("POSTGRES_DB", "capstone_db")
    user = os.getenv("FLASK_DB_ID", "flask_server")
    pw = os.getenv("FLASK_DB_PW")
    host = "postgresql" # 도커에서만 작동

    #todo: env 파일 없을떄 예외처리 raise ValueError
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user}:{pw}@{host}:5432/{db}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    pg_alchemy.init_app(app)

def test_raw_db_connection():
    db = os.getenv("POSTGRES_DB", "capstone_db")
    user = os.getenv("FLASK_DB_ID", "flask_server")
    pw = os.getenv("FLASK_DB_PW")
    host = os.getenv("DB_HOST", "localhost") 

    if not pw:
        raise ValueError("❌ DB 비밀번호(FLASK_DB_PW)가 설정되지 않았습니다.")

    db_url = f'postgresql://{user}:{pw}@{host}:5432/{db}'
    
    engine = create_engine(db_url)

    try:
        with engine.connect() as connection:
            query = text("SELECT * FROM test;")
            result = connection.execute(query).fetchone()
            print(f"연결 성공: {result[0]}")

    except Exception as e:
        print(f"연결 실패: {e}")

if __name__ == "__main__":
    test_raw_db_connection()