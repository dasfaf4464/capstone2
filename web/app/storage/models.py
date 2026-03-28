from flask_login import UserMixin
from .core.pg import pg_alchemy as db


class User(UserMixin, db.Model):
    """회원 테이블"""
    __tablename__ = 'users'

    user_id    = db.Column(db.String(30), primary_key=True)
    user_pw    = db.Column(db.String(30), nullable=False)
    user_email = db.Column(db.String(50), nullable=False)
    user_uuid  = db.Column(db.Integer, db.Sequence('users_user_uuid_seq'), unique=True, nullable=False)

    images = db.relationship('Image', backref='owner', lazy=True, cascade='all, delete')

    def get_id(self):
        return self.user_id

    def __repr__(self):
        return f'<User {self.user_id}>'


class ImageTag(db.Model):
    """태그 테이블"""
    __tablename__ = 'image_tags'

    tag_uuid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tag_name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Tag {self.tag_name}>'


class Image(db.Model):
    """사진 저장 테이블"""
    __tablename__ = 'images'

    image_uuid  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    image_path  = db.Column(db.Text, nullable=False)
    image_query = db.Column(db.Text)
    user_uuid   = db.Column(db.Integer, db.ForeignKey('users.user_uuid'), nullable=False)

    tags = db.relationship('ImageTag', secondary='image_tag_map', lazy=True)

    def __repr__(self):
        return f'<Image {self.image_uuid}>'


class ImageTagMap(db.Model):
    """사진-태그 매핑 테이블"""
    __tablename__ = 'image_tag_map'

    image_uuid = db.Column(db.Integer, db.ForeignKey('images.image_uuid'), primary_key=True)
    tag_uuid   = db.Column(db.Integer, db.ForeignKey('image_tags.tag_uuid'), primary_key=True)