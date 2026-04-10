from ..core.pg import pg_alchemy as db


class Image(db.Model):
    #images 테이블 alchemy
    __tablename__ = "images"

    image_uuid        = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    image_path        = db.Column(db.Text, nullable=False)
    image_query       = db.Column(db.Text, nullable=False)
    image_description = db.Column(db.Text)
    image_create_time = db.Column(db.DateTime(timezone=True), server_default=db.text("now()"))
    is_selected = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    user_uuid         = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.user_uuid"), nullable=False)


def save_image(image_path: str, user_uuid, image_query: str) -> "Image | None":
    #사진 저장 함수
    #경로, user_uuid, 쿼리로 저장
    #나머지는 디폴트
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
        print(f"[save_image] 오류: {e}")
        return None


def get_images_by_user(user_uuid) -> list:
    #user_uuid로 사진 조회 함수
    return Image.query.filter_by(user_uuid=user_uuid).all()

#일단 사진을 다 저장하고 나중에 select한 사진에 대해서 true로
#그리고 검색할때 true인 사진들만 대상으로 하는짓 안하려면
#사진 어떻게 다룰 지 정해야할듯