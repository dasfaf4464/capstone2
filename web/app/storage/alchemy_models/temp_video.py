from ..core.pg import pg_alchemy as db


class TempVideo(db.Model):
    """임시 영상 테이블"""
    __tablename__ = 'temp_video'

    video_uuid      = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    video_file_name = db.Column(db.Text, unique=True, nullable=False)
    video_save_time = db.Column(db.DateTime(timezone=True), server_default=db.text("now()"))

    def __repr__(self):
        return f'<TempVideo {self.video_file_name}>'


def save_temp_video(file_name: str) -> 'TempVideo | None':
    """임시 영상 저장"""
    try:
        video = TempVideo(video_file_name=file_name)
        db.session.add(video)
        db.session.commit()
        return video
    except Exception as e:
        db.session.rollback()
        print(f'[save_temp_video] 오류: {e}')
        return None


def get_temp_video(video_uuid) -> 'TempVideo | None':
    """임시 영상 조회"""
    return TempVideo.query.get(video_uuid)


def get_temp_video_by_name(file_name: str) -> 'TempVideo | None':
    """파일명으로 임시 영상 조회"""
    return TempVideo.query.filter_by(video_file_name=file_name).first()


def delete_temp_video(video_uuid) -> bool:
    """임시 영상 삭제"""
    try:
        video = get_temp_video(video_uuid)
        if not video:
            return False
        db.session.delete(video)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f'[delete_temp_video] 오류: {e}')
        return False