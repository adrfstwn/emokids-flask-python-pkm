from apps import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(64), default='user')
    whatsapp_number = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Siswa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_siswa = db.Column(db.Integer, index=True)
    name = db.Column(db.String(64), index=True, unique=False)
    birth_date = db.Column(db.Date, nullable=False)
    kelas = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Siswa {self.name}>'
    
class ExpresionData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    expresion = db.Column(db.String(128), nullable=False)
    confidence = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<ExpresionData {self.expresion}>'
    
class PoseData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    pose = db.Column(db.String(128), nullable=False)
    confidence = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<PoseData {self.pose}>'
    
class ActiveAdminSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(255), nullable=False, unique=True)

    def __repr__(self):
        return f'<ActiveAdminSession {self.admin_id}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
