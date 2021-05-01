# Import module models
from ..models.user import *
from ..models.session import *
from app import db

def get_user_by_username(username):
    return User.query.filter(User.username == username).first()

def get_user_by_session_token(session_token):
    return User.query.filter(User.session_token == session_token).first()

def get_user_by_update_token(update_token):
    return User.query.filter(User.update_token == update_token).first()

def verify_credentials(username, password):
    optional_user = get_user_by_username(username)

    if optional_user is None:
        return False, None

    return optional_user.verify_password(password), optional_user

def login(username, password):
    if username is None or password is None: 
        return json.dumps({"error": "Invalid username or password"})

    was_successful, user = verify_credentials(username, password)

    if not was_successful:
        return json.dumps({"error": "Incorrect username or password"})

    session = get_session_by_user_id(user.id)

    return json.dumps(
        {
            "user_id": session.user_id,
            "session_token": session.session_token,
            "update_token": session.update_token,
            "expires_at": session.expires_at
        }
    )

def create_user(username, fname, lname, password):
    optional_user = get_user_by_username(username)

    if optional_user is not None:
        return False, optional_user

    user = User(username=username, fname=fname, lname=lname, password=password)
    db.session.add(user)
    db.session.commit()
    
    user_id = user.id
    sess = Session(user=user, user_id=user_id)
    db.session.add(sess)
    db.session.commit()

    return True, user