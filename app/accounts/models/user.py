from . import *
import bcrypt

class User(Base):
  __tablename__ = 'users'

  email           = db.Column(db.String(128), nullable =False, unique =True)
  fname           = db.Column(db.String(128), nullable =False)
  lname           = db.Column(db.String(128), nullable =False)
  password_digest = db.Column(db.LargeBinary, nullable =False)

  def __init__(self, **kwargs):
    self.email           = kwargs.get('email', None)
    self.fname           = kwargs.get('fname', None)
    self.lname           = kwargs.get('lname', None)
    self.password_digest = bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(rounds=13))

  def __repr__(self):
    return str(self.__dict__)

  def verify_password(self, password):
    return bcrypt.checkpw(password.encode('utf8'), self.password_digest)

class UserSchema(ModelSchema):
  class Meta:
    model = User
