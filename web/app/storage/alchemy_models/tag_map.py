from ..core.pg import pg_alchemy as db


class ImageTagMap(db.Model):
    """사진-태그 매핑 테이블"""
    __tablename__ = 'image_tag_map'

    image_uuid = db.Column(db.UUID(as_uuid=True), db.ForeignKey('images.image_uuid'), primary_key=True)
    tag_uuid   = db.Column(db.UUID(as_uuid=True), db.ForeignKey('image_tags.tag_uuid'), primary_key=True)

    def __repr__(self):
        return f'<ImageTagMap image={self.image_uuid} tag={self.tag_uuid}>'


def add_tag_to_image(image_uuid, tag_uuid) -> bool:
    """이미지에 태그 추가"""
    try:
        existing = ImageTagMap.query.filter_by(
            image_uuid=image_uuid, tag_uuid=tag_uuid
        ).first()
        if existing:
            return True
        mapping = ImageTagMap(image_uuid=image_uuid, tag_uuid=tag_uuid)
        db.session.add(mapping)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f'[add_tag_to_image] 오류: {e}')
        return False


def get_tags_by_image(image_uuid) -> list:
    """이미지에 붙은 태그 목록 조회"""
    from .tag import ImageTag
    return db.session.query(ImageTag).join(
        ImageTagMap, ImageTag.tag_uuid == ImageTagMap.tag_uuid
    ).filter(ImageTagMap.image_uuid == image_uuid).all()


def get_images_by_tag(tag_name: str, user_uuid=None) -> list:
    """태그 이름으로 이미지 검색"""
    from .tag import ImageTag
    from .image import Image
    query = db.session.query(Image).join(
        ImageTagMap, Image.image_uuid == ImageTagMap.image_uuid
    ).join(
        ImageTag, ImageTagMap.tag_uuid == ImageTag.tag_uuid
    ).filter(ImageTag.tag_name == tag_name)
    if user_uuid:
        query = query.filter(Image.user_uuid == user_uuid)
    return query.all()


def remove_tag_from_image(image_uuid, tag_uuid) -> bool:
    """이미지에서 태그 제거"""
    try:
        mapping = ImageTagMap.query.filter_by(
            image_uuid=image_uuid, tag_uuid=tag_uuid
        ).first()
        if not mapping:
            return False
        db.session.delete(mapping)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f'[remove_tag_from_image] 오류: {e}')
        return False