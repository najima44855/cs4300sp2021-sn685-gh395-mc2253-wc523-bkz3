# Import module models
from ..models.user import *
from ..models.session import *
from app import db

def get_session_by_user_id(user_id):
    return Session.query.filter(Session.user_id == user_id).first()
  
def get_session_by_update_token(update_token):
    return Session.query.filter(Session.update_token == update_token).first()

def renew_session(update_token):
    user = get_user_by_update_token(update_token)
    session = get_session_by_update_token(update_token)

    if session is None:
        raise Exception('Invalid update token')
    
    session.session_token = session._urlsafe_base_64()
    session.expires_at = datetime.datetime.now() + datetime.timedelta(days=7)
    session.update_token = session._urlsafe_base_64()

    db.session.commit()
    return user