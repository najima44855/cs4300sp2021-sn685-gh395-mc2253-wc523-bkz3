from . import *

class Favorites(Base):
  __tablename__ = 'favorites'

  user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), unique =True, index =True)
  title           = db.Column(db.String(128), nullable =False)
  img_url         = db.Column(db.String(128), nullable =False)

  def __init__(self, **kwargs):
    user = kwargs.get('user', None)
    if user is None:
      raise Exception() # Shouldn't be the case
    self.user_id       = kwargs.get('user_id')
    self.title         = kwargs.get('title')
    self.img_url       = kwargs.get('img_url')

  def __repr__(self):
    return str(self.__dict__)

class FavoritesSchema(ModelSchema):
  class Meta:
    model = Favorites
