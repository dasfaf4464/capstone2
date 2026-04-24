"""
[ photos 모델 ]
사진 테이블 ORM 모델
AI 분석 결과 포함한 사진 정보 관리
"""

import uuid
from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy import TIMESTAMP
from ..core.pg import pg_alchemy as db


class Photo(db.Model):
    __tablename__ = 'photos'

    photo_uuid      = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    travel_uuid     = Column(UUID(as_uuid=True), ForeignKey('travels.travel_uuid', ondelete='CASCADE'), nullable=False)
    user_uuid       = Column(UUID(as_uuid=True), ForeignKey('users.user_uuid', ondelete='CASCADE'), nullable=False)

    # 파일
    photo_path      = Column(Text, nullable=False)

    # AI 분석 상태
    analysis_status = Column(String(10), default='pending')  # pending / done / fail

    # AI 분석 결과
    main_category   = Column(String(20), nullable=True)   # 풍경/장소 / 음식 / 기록
    sub_categories  = Column(JSONB, nullable=True)        # ["바다", "일몰", "모래사장"]
    has_person      = Column(Boolean, nullable=True)      # 인물 포함 여부
    activity        = Column(String(50), nullable=True)   # 하이킹 / null

    created_at      = Column(TIMESTAMP(timezone=True), server_default=func.now())


def save_photo(travel_uuid, user_uuid, photo_path):
    """사진 저장 (분석 전 pending 상태)"""
    try:
        photo = Photo(
            travel_uuid=travel_uuid,
            user_uuid=user_uuid,
            photo_path=photo_path,
            analysis_status='pending',
        )
        db.session.add(photo)
        db.session.commit()
        return photo
    except Exception as e:
        db.session.rollback()
        raise e


def update_analysis_result(photo_uuid, main_category, sub_categories, has_person, activity):
    """AI 분석 결과 저장"""
    try:
        photo = Photo.query.filter_by(photo_uuid=photo_uuid).first()
        if photo:
            photo.main_category  = main_category
            photo.sub_categories = sub_categories
            photo.has_person     = has_person
            photo.activity       = activity
            photo.analysis_status = 'done'
            db.session.commit()
        return photo
    except Exception as e:
        db.session.rollback()
        raise e


def update_analysis_fail(photo_uuid):
    """AI 분석 실패 처리"""
    try:
        photo = Photo.query.filter_by(photo_uuid=photo_uuid).first()
        if photo:
            photo.analysis_status = 'fail'
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def get_photos_by_travel(travel_uuid):
    """여행별 사진 목록 조회"""
    return Photo.query.filter_by(travel_uuid=travel_uuid).order_by(Photo.created_at.asc()).all()


def get_photo(photo_uuid):
    """사진 단건 조회"""
    return Photo.query.filter_by(photo_uuid=photo_uuid).first()


def search_photos_by_keyword(user_uuid, keyword):
    """부카테고리 키워드로 사진 검색"""
    return Photo.query.filter(
        Photo.user_uuid == user_uuid,
        Photo.sub_categories.contains([keyword])
    ).order_by(Photo.created_at.desc()).all()


def get_category_stats(user_uuid):
    """유저의 주카테고리별 사진 수 집계"""
    from sqlalchemy import text
    from ..core.pg import pg_alchemy as db
    result = db.session.execute(
        text("""
            SELECT main_category, COUNT(*) as cnt
            FROM photos
            WHERE user_uuid = :user_uuid
              AND analysis_status = 'done'
              AND main_category IS NOT NULL
            GROUP BY main_category
        """),
        {'user_uuid': str(user_uuid)}
    ).fetchall()
    return {row[0]: row[1] for row in result}


def get_keyword_stats(user_uuid, limit=10):
    """유저의 부카테고리 키워드 상위 N개 집계"""
    from sqlalchemy import text
    result = db.session.execute(
        text("""
            SELECT keyword, COUNT(*) as cnt
            FROM photos,
                 jsonb_array_elements_text(sub_categories) as keyword
            WHERE user_uuid = :user_uuid
              AND analysis_status = 'done'
            GROUP BY keyword
            ORDER BY cnt DESC
            LIMIT :limit
        """),
        {'user_uuid': str(user_uuid), 'limit': limit}
    ).fetchall()
    return [{'keyword': row[0], 'count': row[1]} for row in result]
