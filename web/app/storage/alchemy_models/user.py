from ..core.pg import pg_alchemy as db


class User(db.Model):
    #users 테이블 alchemy
    __tablename__ = "users"

    user_uuid        = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    user_id          = db.Column(db.String(30), nullable=False, unique=True)
    user_pw          = db.Column(db.String(30), nullable=False)
    user_create_time = db.Column(db.DateTime(timezone=True), server_default=db.text("now()"), nullable=False)


def signup(user_id: str, user_pw: str) -> "User | None":
    # 유저 생성 후 DB 저장, 중복 ID면 rollback 후 None 반환
    try:
        user = User(user_id=user_id, user_pw=user_pw)
        db.session.add(user)
        db.session.commit()
        return user
    except Exception as e:
        db.session.rollback()
        print(f"[signup] 오류: {e}")
        return None


def login(user_id: str, user_pw: str) -> "User | None":
    # user_id로 유저 조회 후 pw 일치 확인, 성공 시 User 객체 반환 실패 시 None
    user = User.query.filter_by(user_id=user_id).first()
    if not user or user.user_pw != user_pw:
        return None
    return user


#def logout() -> bool: 라우트에서 쿠키 지우면 끝이어서 세션을 위한 db정의 필요 없고 로그아웃 함수도 필요 없음


def get_user(user_uuid) -> "User | None":
    # user_uuid로 유저 단건 조회
    return User.query.get(user_uuid)