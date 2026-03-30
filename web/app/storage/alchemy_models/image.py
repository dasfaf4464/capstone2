from ..core.pg import pg_alchemy as db


class Image(db.Model):
    """사진 저장 테이블"""
    __tablename__ = 'images'

    image_uuid        = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    image_path        = db.Column(db.Text, nullable=False)
    image_query       = db.Column(db.Text)
    image_create_time = db.Column(db.DateTime(timezone=True), server_default=db.text("now()"))
    user_uuid         = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.user_uuid'), nullable=False)

    tags = db.relationship('ImageTag', secondary='image_tag_map', lazy=True)

    def __repr__(self):
        return f'<Image {self.image_uuid}>'


def save_image(image_path: str, image_query: str, user_uuid) -> 'Image | None':
    """이미지 정보 저장"""
    try:
        image = Image(
            image_path=image_path,
            image_query=image_query,
            user_uuid=user_uuid,
        )
        db.session.add(image)
        db.session.commit()
        return image
    except Exception as e:
        db.session.rollback()
        print(f'[save_image] 오류: {e}')
        return None


def get_image(image_uuid) -> 'Image | None':
    """특정 이미지 조회"""
    return Image.query.get(image_uuid)


def get_images_by_user(user_uuid) -> list:
    """유저의 이미지 목록 조회"""
    return Image.query.filter_by(user_uuid=user_uuid).all()


def delete_image(image_uuid) -> bool:
    """이미지 삭제"""
    try:
        image = get_image(image_uuid)
        if not image:
            return False
        db.session.delete(image)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f'[delete_image] 오류: {e}')
        return False