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

-- =============================================
-- 테이블 생성
-- =============================================

-- 회원 정보 테이블
CREATE TABLE IF NOT EXISTS users (
    user_uuid        UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          VARCHAR(30)  NOT NULL UNIQUE,
    user_pw          VARCHAR(30)  NOT NULL,
    user_create_time TIMESTAMPTZ  DEFAULT now()
);

-- 여행 테이블
CREATE TABLE IF NOT EXISTS travels (
    travel_uuid      UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_uuid        UUID         NOT NULL REFERENCES users(user_uuid) ON DELETE CASCADE,

    travel_name      VARCHAR(100) NOT NULL,   -- 여행 이름 (사용자 입력)
    start_date       DATE         NOT NULL,   -- 여행 시작일 (사용자 입력)
    end_date         DATE         NOT NULL,   -- 여행 종료일 (사용자 입력)
    cover_photo_path TEXT,                   -- 대표 썸네일 (첫 번째 사진 자동 지정)

    created_at       TIMESTAMPTZ  DEFAULT now()
);

-- 사진 테이블
CREATE TABLE IF NOT EXISTS photos (
    photo_uuid       UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    travel_uuid      UUID         NOT NULL REFERENCES travels(travel_uuid) ON DELETE CASCADE,
    user_uuid        UUID         NOT NULL REFERENCES users(user_uuid) ON DELETE CASCADE,

    -- 파일
    photo_path       TEXT         NOT NULL,   -- 사진 저장 경로

    -- AI 분석 상태
    analysis_status  VARCHAR(10)  DEFAULT 'pending',  -- pending / done / fail

    -- AI 분석 결과
    main_category    VARCHAR(20),              -- 풍경/장소 / 음식 / 기록
    sub_categories   JSONB,                   -- ["바다", "일몰", "모래사장"]
    has_person       BOOLEAN,                 -- 인물 포함 여부 (true / false)
    activity         VARCHAR(50),             -- 하이킹 / 수상스포츠 / null

    created_at       TIMESTAMPTZ  DEFAULT now()
);

-- 부카테고리 검색 성능을 위한 GIN 인덱스
CREATE INDEX IF NOT EXISTS idx_photos_sub_categories
ON photos USING GIN (sub_categories);

-- 사용자 통계 테이블
CREATE TABLE IF NOT EXISTS user_stats (
    user_uuid        UUID         PRIMARY KEY REFERENCES users(user_uuid) ON DELETE CASCADE,

    -- 통계 (사진 업로드 완료 시 갱신)
    category_stats   JSONB,       -- {"풍경/장소": 62, "음식": 25, "기록": 13}
    keyword_stats    JSONB,       -- [{"keyword":"바다","count":25}, ...] 상위 10개

    -- LLM 결과 (통계 갱신 시 재생성)
    personality_type VARCHAR(100),-- "당신은 자연을 사랑하는 여행자입니다"
    recommendation   TEXT,        -- "바다와 미식을 동시에 즐길 수 있는..."

    updated_at       TIMESTAMPTZ  DEFAULT now()
);
