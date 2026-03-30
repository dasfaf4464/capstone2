from ..core.pg import pg_alchemy as db


class User(db.Model):
    """회원 정보 테이블"""
    __tablename__ = 'users'

    user_uuid           = db.Column(db.UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"))
    user_nickname       = db.Column(db.String(30), nullable=False, unique=True)
    user_pw             = db.Column(db.String(30), nullable=False)
    user_email          = db.Column(db.String(50))
    user_create_time    = db.Column(db.DateTime(timezone=True), server_default=db.text("now()"), nullable=False)
    user_last_conn_time = db.Column(db.DateTime(timezone=True))

    images = db.relationship('Image', backref='owner', lazy=True, cascade='all, delete')

    def get_id(self):
        return str(self.user_uuid)

    def __repr__(self):
        return f'<User {self.user_nickname}>'


def create_user(nickname: str, pw: str, email: str = None) -> bool:
    """새로운 회원 정보를 저장합니다."""
    try:
        user = User(
            user_nickname=nickname,
            user_pw=pw,
            user_email=email,
        )
        db.session.add(user)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f'[create_user] 오류: {e}')
        return False


def get_user_by_nickname(nickname: str):
    """닉네임으로 유저 조회"""
    return User.query.filter_by(user_nickname=nickname).first()


def get_user_by_uuid(user_uuid) -> 'User':
    """UUID로 유저 조회"""
    return User.query.get(user_uuid)


def login(nickname: str, pw: str) -> bool:
    """닉네임과 비밀번호로 로그인 검증"""
    user = get_user_by_nickname(nickname)
    if not user or user.user_pw != pw:
        return False
    return True


def update_last_conn(user_uuid) -> bool:
    """마지막 접속 시간 업데이트"""
    try:
        user = get_user_by_uuid(user_uuid)
        if not user:
            return False
        user.user_last_conn_time = db.func.now()
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f'[update_last_conn] 오류: {e}')
        return False


def delete_user(user_uuid) -> bool:
    """회원 탈퇴"""
    try:
        user = get_user_by_uuid(user_uuid)
        if not user:
            return False
        db.session.delete(user)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f'[delete_user] 오류: {e}')
        return False