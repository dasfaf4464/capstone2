from ..core.pg import pg_alchemy as db


class TempVideo(db.Model):
    #temp_video 테이블 alchemy
    __tablename__ = "temp_video"

    video_uuid      = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    video_path      = db.Column(db.Text, nullable=False)
    video_save_time = db.Column(db.DateTime(timezone=True), server_default=db.text("now()"))
    user_uuid       = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.user_uuid"), nullable=False)


def save_temp_video(video_path: str, user_uuid) -> "TempVideo | None":
    #영상 저장 함수
    try:
        video = TempVideo(video_path=video_path, user_uuid=user_uuid)
        db.session.add(video)
        db.session.commit()
        return video
    except Exception as e:
        db.session.rollback()
        print(f"[save_temp_video] 오류: {e}")
        return None


def get_temp_video(video_uuid) -> "TempVideo | None":
    #video_uuid로 임시 영상 조회(영상처리할때)
    return TempVideo.query.get(video_uuid)