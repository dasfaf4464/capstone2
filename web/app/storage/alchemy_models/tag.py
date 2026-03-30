from ..core.pg import pg_alchemy as db


class ImageTag(db.Model):
    """태그 테이블"""
    __tablename__ = 'image_tags'

    tag_uuid = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    tag_name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Tag {self.tag_name}>'


def create_tag(tag_name: str) -> 'ImageTag | None':
    """태그 생성 (이미 있으면 기존 태그 반환)"""
    tag = get_tag(tag_name)
    if tag:
        return tag
    try:
        tag = ImageTag(tag_name=tag_name)
        db.session.add(tag)
        db.session.commit()
        return tag
    except Exception as e:
        db.session.rollback()
        print(f'[create_tag] 오류: {e}')
        return None


def get_tag(tag_name: str) -> 'ImageTag | None':
    """태그 이름으로 조회"""
    return ImageTag.query.filter_by(tag_name=tag_name).first()


def get_tag_by_uuid(tag_uuid) -> 'ImageTag | None':
    """UUID로 태그 조회"""
    return ImageTag.query.get(tag_uuid)


def get_all_tags() -> list:
    """전체 태그 목록 조회"""
    return ImageTag.query.all()