from flask import *
#from session import SqliteSessionInterface
import os
app = Flask(__name__)
app.config.update(dict(
SQLALCHEMY_DATABASE_URI='sqlite:///{0}'.format(os.path.join(app.root_path, 'second_lab.db')),
DEBUG=True
))
app.secret_key = "key for flask"
from sqlite3 import dbapi2 as sqlite
from sqlalchemy.orm import sessionmaker, aliased
from datetime import datetime, timedelta
import hashlib, string, random
#here are models for the db
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import *
db = SQLAlchemy(app)

#Models

def make_random_string(size):
    return ''.join([random.choice(string.ascii_letters) for i in range(size)])

class User(db.Model):
    __tablename__ = "user"
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer(), primary_key = True)
    username = Column(String(100), unique=True)
    password = Column(String(256))
    email = Column(String(200))
    phone = Column(String(11))
    sessions = relationship("UserSession", cascade="all, delete-orphan")
    goods = relationship("Good")
    comments = relationship("Comment")
    
    def __init__(self, username, password, phone, email):
        self.username = username
        self.password = password
        self.email = email
        self.phone = phone

    def __repr__(self):
        return 'id: {0}, username: {1}, email: {2}, phone: {3}'.format(self.id, self.username, self.email, self.phone)
    
    def to_dict(self):
        return {'id': self.id, 'username': self.username, 'password': self.password, 'email': self.email, 'phone': self.phone}

class UserSession(db.Model):
    __tablename__ = "usersession"
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer(), primary_key = True)
    session_id = Column(String(32), unique = True)
    timestamp = Column(DateTime)
    user_id = Column(ForeignKey("user.id"), nullable=False)
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.refresh()
   
    def refresh(self):
        self.session_id = random_string(32)
        self.timestamp = datetime.utcnow()
   
    def session_expired(self):
        return (self.timestamp - datetime.utcnow()) >= timedelta(hours = 1)

class Good(db.Model):
    __tablename__ = "good"
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer(), primary_key = True)
    author_id = Column(ForeignKey("user.id"), nullable=False)
    description = Column(String(100))
    text = Column(Text())
    comments = relationship("Comment", cascade="all, delete-orphan")
    
    def __init__(self, user_id, description, text):
        self.author_id = user_id
        self.description = description
        self.text = text
        
    def __repr__(self):
        return 'id: {0}, author: {1}, description: {2}'.format(self.id, self.author_id, self.description)

    def to_dict(self):
        return {'id': self.id, 'author_id': self.author_id, 'description': self.description, 'text': self.text}
    

class Comment(db.Model):
    __tablename__ = "comment"
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer(), primary_key = True)
    text = Column(Text())
    author_id = Column(ForeignKey("user.id"), nullable=False)
    good_id = Column(ForeignKey("good.id"), nullable=False)
    deleted = Column(Boolean(), default = False)
    
    def __init__(self, user_id, good_id, text):
        self.author_id = user_id
        self.good_id = good_id
        self.text = text
        
    def __repr__(self):
        return 'id: {0}, author: {1}'.format(self.id, self.author_id)

    def to_dict(self):
        return {'id': self.id, 'author_id': self.author_id, 'good_id': self.good_id, 'text': self.text if not self.deleted else '', 'deleted': self.deleted}
        
    def delete(self):
        self.deleted = True
