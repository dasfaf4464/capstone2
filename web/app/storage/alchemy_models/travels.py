"""
[ travels 모델 ]
여행 그룹 테이블 ORM 모델
사용자가 만든 여행 목록 관리
"""

import uuid
from datetime import date
from sqlalchemy import Column, String, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import TIMESTAMP
from ..core.pg import pg_alchemy as db


class Travel(db.Model):
    __tablename__ = 'travels'

    travel_uuid      = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_uuid        = Column(UUID(as_uuid=True), ForeignKey('users.user_uuid', ondelete='CASCADE'), nullable=False)

    travel_name      = Column(String(100), nullable=False)
    start_date       = Column(Date, nullable=False)
    end_date         = Column(Date, nullable=False)
    cover_photo_path = Column(Text, nullable=True)

    created_at       = Column(TIMESTAMP(timezone=True), server_default=func.now())


def create_travel(user_uuid, travel_name, start_date, end_date):
    """여행 생성"""
    try:
        travel = Travel(
            user_uuid=user_uuid,
            travel_name=travel_name,
            start_date=start_date,
            end_date=end_date,
        )
        db.session.add(travel)
        db.session.commit()
        return travel
    except Exception as e:
        db.session.rollback()
        raise e


def get_travels_by_user(user_uuid):
    """유저의 여행 목록 전체 조회 (최신순)"""
    return Travel.query.filter_by(user_uuid=user_uuid).order_by(Travel.created_at.desc()).all()


def get_travel(travel_uuid):
    """여행 단건 조회"""
    return Travel.query.filter_by(travel_uuid=travel_uuid).first()


def update_cover_photo(travel_uuid, photo_path):
    """대표 썸네일 업데이트"""
    try:
        travel = Travel.query.filter_by(travel_uuid=travel_uuid).first()
        if travel and not travel.cover_photo_path:
            travel.cover_photo_path = photo_path
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e
