from sqlalchemy import Column, Integer, String, Text

from database import Base

class User(Base):
    """
    Defines the users table in the NoticeMe database.
    """
    __tablename__ = 'users'
    userid = Column(Integer, nullable=False, primary_key=True)
    email = Column(String(250), nullable=False)
    freq = Column(String(10), nullable=False)
    autoadd = Column(Integer, nullable=False)
    citywide = Column(Integer, nullable=False)

class Notice(Base):
    """
    Defines the notices table in the NoticeMe database.
    """
    __tablename__ = 'notices'
    noticeid = Column(Integer, nullable=False, primary_key=True)
    userid = Column(Integer, nullable=False)
    namehash = Column(String(50), nullable=False)
    name = Column(String(250), nullable=False)
    notices = Column(Text(), nullable=False)
    geom = Column(Text(), nullable=False)
