-- 애드온 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 플라스크 서버 유저 생성
CREATE USER flask_server WITH PASSWORD 'flask_pw';
GRANT CONNECT ON DATABASE capstone_db TO flask_server;
GRANT USAGE ON SCHEMA public TO flask_server;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO flask_server;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO flask_server;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO flask_server;

-- 테이블 생성

-- 회원 정보 테이블
CREATE TABLE IF NOT EXISTS users (
    user_uuid          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_nickname      VARCHAR(30) NOT NULL UNIQUE,
    user_pw            VARCHAR(30) NOT NULL,
    user_email         VARCHAR(50),
    user_create_time   timestamptz DEFAULT now(),
    user_last_conn_time timestamptz
);

-- 태그 테이블
CREATE TABLE IF NOT EXISTS image_tags (
    tag_uuid uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    tag_name VARCHAR(50) UNIQUE NOT NULL
);

-- 사진 저장 테이블
CREATE TABLE IF NOT EXISTS images (
    image_uuid        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    image_path        TEXT NOT NULL,
    image_query       TEXT,
    image_create_time timestamptz DEFAULT now(),
    user_uuid         uuid REFERENCES users(user_uuid) ON DELETE CASCADE
);

-- 사진-태그 매핑 테이블
CREATE TABLE IF NOT EXISTS image_tag_map (
    image_uuid uuid REFERENCES images(image_uuid) ON DELETE CASCADE,
    tag_uuid   uuid REFERENCES image_tags(tag_uuid) ON DELETE CASCADE,
    PRIMARY KEY (image_uuid, tag_uuid)
);

-- 임시 영상 테이블 (AI 분석용)
CREATE TABLE IF NOT EXISTS temp_video (
    video_uuid      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    video_file_name TEXT UNIQUE NOT NULL,
    video_save_time timestamptz DEFAULT now()
);

-- 임시 이미지 테이블 (AI 분석 결과)
CREATE TABLE IF NOT EXISTS temp_image (
    image_uuid      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    image_file_name TEXT UNIQUE NOT NULL,
    image_save_time timestamptz DEFAULT now()
);

-- 시퀀스 권한 부여
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO flask_server;
