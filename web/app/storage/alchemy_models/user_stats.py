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


def get_user_stats(user_uuid):
    """유저 통계 조회"""
    return UserStats.query.filter_by(user_uuid=user_uuid).first()


def upsert_user_stats(user_uuid, category_stats, keyword_stats, personality_type, recommendation):
    """유저 통계 저장 또는 갱신"""
    try:
        stats = UserStats.query.filter_by(user_uuid=user_uuid).first()
        if stats:
            stats.category_stats   = category_stats
            stats.keyword_stats    = keyword_stats
            stats.personality_type = personality_type
            stats.recommendation   = recommendation
            stats.updated_at       = func.now()
        else:
            stats = UserStats(
                user_uuid=user_uuid,
                category_stats=category_stats,
                keyword_stats=keyword_stats,
                personality_type=personality_type,
                recommendation=recommendation,
            )
            db.session.add(stats)
        db.session.commit()
        return stats
    except Exception as e:
        db.session.rollback()
        raise e
