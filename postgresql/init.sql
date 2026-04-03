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
    user_id VARCHAR(30) NOT NULL UNIQUE, -- nickname에서 id로
    user_pw VARCHAR(30) NOT NULL,
    -- user_email VARCHAR(50) NOT NULL,
    user_uuid uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_create_time timestamptz DEFAULT now()
);

/*
-- 태그 테이블
CREATE TABLE IF NOT EXISTS image_tags (
    tag_uuid uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tag_name VARCHAR(50) UNIQUE NOT NULL
);
*/

-- 사진 저장 테이블
CREATE TABLE IF NOT EXISTS images (
    image_uuid uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    image_path TEXT NOT NULL, --서버 저장 경로
    image_query TEXT NOT NULL, -- 사용자 입력 문장
    image_description TEXT, -- llm 설명 저장
    image_create_time timestamptz DEFAULT now(),
    is_selected BOOLEAN NOT NULL DEFAULT FALSE, -- 5장의 사진을 위한 임시 사진 테이블이 필요한지 아니면 다 사진에 저장하고 한장만 선택해서 true로 바꿀지...
    user_uuid UUID REFERENCES users(user_uuid) ON DELETE CASCADE -- 외래키 쓸 떄 타입 같아야 한다고 합니다
);

/*
-- 사진-태그 매핑 테이블
CREATE TABLE IF NOT EXISTS image_tag_map (
    image_uuid uuid REFERENCES images(image_uuid) ON DELETE CASCADE,
    tag_uuid uuid REFERENCES image_tags(tag_uuid) ON DELETE CASCADE,
    
    PRIMARY KEY (image_uuid, tag_uuid)
);
*/

CREATE TABLE IF NOT EXISTS temp_video (
    video_uuid uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    video_path TEXT NOT NULL, -- 서버 저장 경로
    video_save_time timestamptz DEFAULT now(),
    user_uuid UUID REFERENCES users(user_uuid) ON DELETE CASCADE
);

/*
CREATE TABLE if NOT EXISTS temp_image (
    image_uuid uuid PRIMARY KEY DEFAULT gen_random_uuid()
    image_file_name TEXT UNIQUE NOT NULL
    image_save_time timestampz DEFAULT now()
);
*/