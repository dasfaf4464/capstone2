"""
[ user_stats 모델 ]
사용자 통계 + LLM 결과 캐싱 테이블
사진 업로드 완료 시 갱신됨
"""

import uuid
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy import TIMESTAMP
from ..core.pg import pg_alchemy as db


class UserStats(db.Model):
    __tablename__ = 'user_stats'

    user_uuid        = Column(UUID(as_uuid=True), ForeignKey('users.user_uuid', ondelete='CASCADE'), primary_key=True)

    # 통계 (사진 업로드 완료 시 갱신)
    category_stats   = Column(JSONB, nullable=True)  # {"풍경/장소": 62, "음식": 25, "기록": 13}
    keyword_stats    = Column(JSONB, nullable=True)  # [{"keyword":"바다","count":25}, ...]

    # LLM 결과
    personality_type = Column(String(100), nullable=True)  # "당신은 자연을 사랑하는 여행자입니다"
    recommendation   = Column(Text, nullable=True)         # "바다와 미식을 즐기는..."

    updated_at       = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


def clear_user_stats(user_uuid):
    # 사진이 모두 삭제된 경우 통계·LLM 결과를 전부 NULL로 초기화
    try:
        stats = UserStats.query.filter_by(user_uuid=user_uuid).first()
        if stats:
            stats.category_stats   = None
            stats.keyword_stats    = None
            stats.personality_type = None
            stats.recommendation   = None
            db.session.commit()  # onupdate=func.now() 가 자동으로 updated_at 갱신
    except Exception as e:
        db.session.rollback()
        raise e


def get_user_stats(user_uuid):
    # 유저 통계 단건 조회 (category_stats, keyword_stats, personality_type, recommendation 포함)
    return UserStats.query.filter_by(user_uuid=user_uuid).first()


def upsert_user_stats(user_uuid, category_stats, keyword_stats, personality_type, recommendation):
    # PostgreSQL 네이티브 UPSERT — 동시 다중 업로드 시 race condition 방지
    # ::jsonb 캐스트 대신 CAST() 사용 — SQLAlchemy text() 파서가 :: 를 파라미터로 오인하는 버그 회피
    import json as _json
    from sqlalchemy import text
    try:
        db.session.execute(text("""
            INSERT INTO user_stats
                (user_uuid, category_stats, keyword_stats, personality_type, recommendation)
            VALUES
                (:user_uuid,
                 CAST(:category_stats AS jsonb),
                 CAST(:keyword_stats  AS jsonb),
                 :personality_type,
                 :recommendation)
            ON CONFLICT (user_uuid) DO UPDATE SET
                category_stats   = EXCLUDED.category_stats,
                keyword_stats    = EXCLUDED.keyword_stats,
                personality_type = EXCLUDED.personality_type,
                recommendation   = EXCLUDED.recommendation
        """), {
            'user_uuid':        str(user_uuid),
            'category_stats':   _json.dumps(category_stats,  ensure_ascii=False),
            'keyword_stats':    _json.dumps(keyword_stats,   ensure_ascii=False),
            'personality_type': personality_type,
            'recommendation':   recommendation,
        })
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e
