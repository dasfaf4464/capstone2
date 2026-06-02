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
    # 사진 레코드 생성 (analysis_status='pending', AI 분석 전 초기 상태)
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
    # AI 분석 결과(카테고리·키워드·인물·활동) 저장 후 status를 done으로 변경
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
    # AI 분석 실패 시 status를 fail로 변경
    try:
        photo = Photo.query.filter_by(photo_uuid=photo_uuid).first()
        if photo:
            photo.analysis_status = 'fail'
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def reset_to_pending(photo_uuid):
    # 실패한 사진의 분석 결과를 초기화하고 status를 pending으로 재설정
    try:
        photo = Photo.query.filter_by(photo_uuid=photo_uuid).first()
        if photo:
            photo.analysis_status = 'pending'
            photo.main_category   = None
            photo.sub_categories  = None
            photo.has_person      = None
            photo.activity        = None
            db.session.commit()
        return photo
    except Exception as e:
        db.session.rollback()
        raise e


def get_photos_by_travel(travel_uuid):
    # 여행별 사진 목록 조회 (업로드 순)
    return Photo.query.filter_by(travel_uuid=travel_uuid).order_by(Photo.created_at.asc()).all()


def get_photo(photo_uuid):
    # photo_uuid로 사진 단건 조회
    return Photo.query.filter_by(photo_uuid=photo_uuid).first()


def search_photos_by_keyword(user_uuid, keyword):
    # sub_categories 부분 일치 + activity 부분 일치 통합 검색, 여행명 포함 반환 (최신순)
    from sqlalchemy import text
    pattern = f'%{keyword}%'
    result = db.session.execute(
        text("""
            SELECT DISTINCT
                p.photo_uuid, p.photo_path, p.main_category,
                p.sub_categories, p.has_person, p.activity,
                p.travel_uuid, t.travel_name, p.created_at,
                t.start_date, t.end_date
            FROM photos p
            JOIN travels t ON p.travel_uuid = t.travel_uuid
            WHERE p.user_uuid   = :user_uuid
              AND p.analysis_status = 'done'
              AND (
                (p.sub_categories IS NOT NULL AND EXISTS (
                    SELECT 1 FROM jsonb_array_elements_text(p.sub_categories) AS kw
                    WHERE kw ILIKE :pattern
                ))
                OR p.activity ILIKE :pattern
                OR ('인물포함' ILIKE :pattern AND p.has_person = true)
              )
            ORDER BY p.created_at DESC
        """),
        {'user_uuid': str(user_uuid), 'pattern': pattern}
    ).fetchall()
    return [
        {
            'photo_uuid':     str(row[0]),
            'photo_path':     row[1],
            'main_category':  row[2],
            'sub_categories': row[3] or [],
            'has_person':     row[4],
            'activity':       row[5],
            'travel_uuid':    str(row[6]),
            'travel_name':    row[7],
            # row[8] = created_at (정렬용, 응답에는 미포함)
            'travel_start':   str(row[9])  if row[9]  else None,
            'travel_end':     str(row[10]) if row[10] else None,
        }
        for row in result
    ]


def get_travel_category_stats(travel_uuid):
    # 특정 여행의 main_category별 사진 수 집계 → {"풍경/장소": 10, "음식": 5, ...} 반환
    from sqlalchemy import text
    result = db.session.execute(
        text("""
            SELECT main_category, COUNT(*) as cnt
            FROM photos
            WHERE travel_uuid = :travel_uuid
              AND analysis_status = 'done'
              AND main_category IS NOT NULL
            GROUP BY main_category
        """),
        {'travel_uuid': str(travel_uuid)}
    ).fetchall()
    return {row[0]: row[1] for row in result}


def get_travel_keyword_stats(travel_uuid):
    # 특정 여행의 sub_categories 키워드 빈도 전체 집계 (빈도 내림차순)
    from sqlalchemy import text
    result = db.session.execute(
        text("""
            SELECT keyword, COUNT(*) as cnt
            FROM photos,
                 jsonb_array_elements_text(sub_categories) as keyword
            WHERE travel_uuid = :travel_uuid
              AND analysis_status = 'done'
              AND sub_categories IS NOT NULL
            GROUP BY keyword
            ORDER BY cnt DESC
        """),
        {'travel_uuid': str(travel_uuid)}
    ).fetchall()
    return [{'keyword': row[0], 'count': row[1]} for row in result]


def get_category_stats(user_uuid):
    # 유저의 main_category별 사진 수 집계 → {"풍경/장소": 62, "음식": 25, ...} 반환
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


def get_travel_person_stats(travel_uuid):
    # 여행의 분석 완료 사진 중 인물 포함 수 vs 전체 수 반환
    from sqlalchemy import text
    row = db.session.execute(
        text("""
            SELECT
                COUNT(*) FILTER (WHERE has_person = true) AS with_person,
                COUNT(*) AS total
            FROM photos
            WHERE travel_uuid = :travel_uuid
              AND analysis_status = 'done'
        """),
        {'travel_uuid': str(travel_uuid)}
    ).fetchone()
    return {'with_person': int(row[0]), 'total': int(row[1])}


def get_travel_activity_stats(travel_uuid):
    # 여행의 활동별 사진 수 집계 (activity 있는 사진만)
    from sqlalchemy import text
    result = db.session.execute(
        text("""
            SELECT activity, COUNT(*) as cnt
            FROM photos
            WHERE travel_uuid = :travel_uuid
              AND analysis_status = 'done'
              AND activity IS NOT NULL
            GROUP BY activity
            ORDER BY cnt DESC
        """),
        {'travel_uuid': str(travel_uuid)}
    ).fetchall()
    return [{'activity': row[0], 'count': int(row[1])} for row in result]


def get_user_person_stats(user_uuid):
    # 유저 전체 사진 중 인물 포함 수 vs 전체 수 반환
    from sqlalchemy import text
    row = db.session.execute(
        text("""
            SELECT
                COUNT(*) FILTER (WHERE has_person = true) AS with_person,
                COUNT(*) AS total
            FROM photos
            WHERE user_uuid = :user_uuid
              AND analysis_status = 'done'
        """),
        {'user_uuid': str(user_uuid)}
    ).fetchone()
    return {'with_person': int(row[0]), 'total': int(row[1])}


def get_user_activity_stats(user_uuid):
    # 유저 전체 활동별 사진 수 집계 (activity 있는 사진만)
    from sqlalchemy import text
    result = db.session.execute(
        text("""
            SELECT activity, COUNT(*) as cnt
            FROM photos
            WHERE user_uuid = :user_uuid
              AND analysis_status = 'done'
              AND activity IS NOT NULL
            GROUP BY activity
            ORDER BY cnt DESC
        """),
        {'user_uuid': str(user_uuid)}
    ).fetchall()
    return [{'activity': row[0], 'count': int(row[1])} for row in result]


def get_user_travel_series(user_uuid):
    # 유저의 여행별 카테고리 통계를 시계열(start_date 오름차순)로 반환
    # → [{"travel_name": "제주도", "start_date": "2024-03-01", "category_stats": {"풍경/장소": 10, "음식": 5}}, ...]
    from sqlalchemy import text
    from collections import OrderedDict
    result = db.session.execute(
        text("""
            SELECT t.travel_name, t.start_date, p.main_category, COUNT(*) as cnt
            FROM photos p
            JOIN travels t ON p.travel_uuid = t.travel_uuid
            WHERE p.user_uuid = :user_uuid
              AND p.analysis_status = 'done'
              AND p.main_category IS NOT NULL
            GROUP BY t.travel_uuid, t.travel_name, t.start_date, p.main_category
            ORDER BY t.start_date ASC
        """),
        {'user_uuid': str(user_uuid)}
    ).fetchall()

    series = OrderedDict()
    for row in result:
        key = (str(row[1]), row[0])
        if key not in series:
            series[key] = {'travel_name': row[0], 'start_date': str(row[1]), 'category_stats': {}}
        series[key]['category_stats'][row[2]] = int(row[3])

    return list(series.values())


def get_keyword_stats(user_uuid, limit=10):
    # sub_categories + 인물포함(has_person) + 활동명(activity)을 통합 집계, 상위 N개 반환
    # → [{"keyword":"바다","count":25}, {"keyword":"인물포함","count":7}, {"keyword":"하이킹","count":5}, ...]
    from sqlalchemy import text
    result = db.session.execute(
        text("""
            SELECT keyword, COUNT(*) as cnt
            FROM (
                -- sub_categories 키워드
                SELECT jsonb_array_elements_text(sub_categories) AS keyword
                FROM photos
                WHERE user_uuid = :user_uuid
                  AND analysis_status = 'done'
                  AND sub_categories IS NOT NULL

                UNION ALL

                -- 인물 포함 사진 → '인물포함' 태그로 집계
                SELECT '인물포함' AS keyword
                FROM photos
                WHERE user_uuid = :user_uuid
                  AND analysis_status = 'done'
                  AND has_person = true

                UNION ALL

                -- 활동명 → 그대로 태그로 집계
                SELECT activity AS keyword
                FROM photos
                WHERE user_uuid = :user_uuid
                  AND analysis_status = 'done'
                  AND activity IS NOT NULL
            ) AS all_tags
            GROUP BY keyword
            ORDER BY cnt DESC
            LIMIT :limit
        """),
        {'user_uuid': str(user_uuid), 'limit': limit}
    ).fetchall()
    return [{'keyword': row[0], 'count': row[1]} for row in result]
