# Import module models
from ..models.user import *
from ..models.favorites import *
from .users_controller import *
from app import db

def create_favorites(uname, manga_name, img_url):
    user = get_user_by_username(uname)

    if user is None:
        return False, None

    optional_favorite = Favorites.query.filter(Favorites.title == manga_name, \
        Favorites.user_id == user.id).first()

    if optional_favorite is not None:
        return False, optional_favorite

    favorite = Favorites(user_id=user.id, title=manga_name, img_url=img_url)
    db.session.add(favorite)
    db.session.commit()

    return True, favorite

def remove_favorites(uname, manga_name):
    user = get_user_by_username(uname)

    if user is None:
        return False, None

    optional_favorite = Favorites.query.filter(Favorites.title == manga_name, \
        Favorites.user_id == user.id).first()

    if optional_favorite is None:
        return False, None

    db.session.delete(optional_favorite)
    db.session.commit()

    return True, optional_favorite

def get_favorites(uname):
    user = get_user_by_username(uname)

    favorites = Favorites.query.filter(Favorites.user_id == user.id).all()

    if favorites == []:
        return False, None

    return True, favorites