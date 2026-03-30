from ..core.pg import pg_alchemy as db


class TempImage(db.Model):
    """임시 이미지 테이블"""
    __tablename__ = 'temp_image'

    image_uuid      = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    image_file_name = db.Column(db.Text, unique=True, nullable=False)
    image_save_time = db.Column(db.DateTime(timezone=True), server_default=db.text("now()"))

    def __repr__(self):
        return f'<TempImage {self.image_file_name}>'


def save_temp_image(file_name: str) -> 'TempImage | None':
    """임시 이미지 저장"""
    try:
        image = TempImage(image_file_name=file_name)
        db.session.add(image)
        db.session.commit()
        return image
    except Exception as e:
        db.session.rollback()
        print(f'[save_temp_image] 오류: {e}')
        return None


def get_temp_image(image_uuid) -> 'TempImage | None':
    """임시 이미지 조회"""
    return TempImage.query.get(image_uuid)


def get_temp_image_by_name(file_name: str) -> 'TempImage | None':
    """파일명으로 임시 이미지 조회"""
    return TempImage.query.filter_by(image_file_name=file_name).first()


def delete_temp_image(image_uuid) -> bool:
    """임시 이미지 삭제"""
    try:
        image = get_temp_image(image_uuid)
        if not image:
            return False
        db.session.delete(image)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f'[delete_temp_image] 오류: {e}')
        return False