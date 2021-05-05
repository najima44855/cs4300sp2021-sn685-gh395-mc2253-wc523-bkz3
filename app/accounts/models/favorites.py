from . import *

class Favorites(Base):
  __tablename__ = 'favorites'

  user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), index =True)
  title           = db.Column(db.String(128), nullable =False)
  img_url         = db.Column(db.String(128), nullable =False)
  manga_url       = db.Column(db.String(128), nullable =False)

  def __init__(self, **kwargs):
    self.user_id       = kwargs.get('user_id')
    self.title         = kwargs.get('title')
    self.img_url       = kwargs.get('img_url')
    self.manga_url     = kwargs.get('manga_url')

  def __repr__(self):
    return str(self.__dict__)

class FavoritesSchema(ModelSchema):
  class Meta:
    model = Favorites
