import os
from paths import *

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///{0}/{1}'.format(DATABASE_PATH, 'lab3.db'), convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

from sqlite3 import dbapi2 as sqlite
from sqlalchemy.orm import sessionmaker, aliased, relationship

from datetime import datetime, timedelta
import hashlib, string, random

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import *


def init_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

# models

class User(Base):
    __tablename__ = "user"
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer(), primary_key = True)
    username = Column(String(100), unique=True)
    password = Column(String(256))
    mail = Column(String(200))
    phone = Column(String(11))
    goods = relationship("good")
    comments = relationship("Comment")
    sessions = relationship("UserSession", cascade="all, delete-orphan")
    
    def __init__(self, username, password, phone, mail):
        self.username = username
        self.password = password
        self.mail = mail
        self.phone = phone

    def __repr__(self):
        return 'id: {0}, username: {1}, mail: {2}, phone: {3}'.format(self.id, self.username, self.mail, self.phone)
    
    def to_dict(self):
        return {'id': self.id, 'username': self.username, 'password': self.password, 'mail': self.mail, 'phone': self.phone}

def make_random_string(size):
    return ''.join([random.choice(string.ascii_letters) for i in range(size)])

class Good(Base):
    __tablename__ = "good"
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer(), primary_key = True)
    description = Column(String(100))
    text = Column(Text())
    author_id = Column(ForeignKey("user.id"), nullable=False)
    
    comments = relationship("Comment", cascade="all, delete-orphan")
    
    def __init__(self, user_id, description, text):
        self.author_id = user_id
        self.description = description
        self.text = text
        
    def __repr__(self):
        return 'id: {0}, author: {1}, description: {2}'.format(self.id, self.author_id, self.description)

    def to_dict(self):
        return {'id': self.id, 'author_id': self.author_id, 'description': self.description, 'text': self.text}
    
    def to_dict_short(self):
        return {'id': self.id, 'author_id': self.author_id, 'description': self.description}


class Comment(Base):
    __tablename__ = "comment"
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer(), primary_key = True)
    text = Column(Text())
    author_id = Column(ForeignKey("user.id"), nullable=False)
    good_id = Column(ForeignKey("good.id"), nullable=False)
    is_deleted = Column(Boolean(), default = False)
    
    def __init__(self, user_id, good_id, text):
        self.author_id = user_id
        self.good_id = good_id
        self.text = text
        
    def __repr__(self):
        return 'id: {0}, author: {1}'.format(self.id, self.author_id)

    def to_dict(self):
        return {'id': self.id, 'author_id': self.author_id, 'good_id': self.good_id, 'text': self.text if not self.is_deleted else '', 'is_deleted': self.is_deleted}
        
    def delete(self):
        self.is_deleted = True


class UserSession(Base):
    __tablename__ = "usersession"
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer(), primary_key = True)
    session_id = Column(String(32), unique = True)
    timestamp = Column(DateTime)
    user_id = Column(ForeignKey("user.id"), nullable=False)
    
    def session_expired(self):
        return (self.timestamp - datetime.utcnow()) >= timedelta(hours = 1)
   
    def refresh(self):
        self.session_id = make_random_string(32)
        self.timestamp = datetime.utcnow()
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.refresh()

