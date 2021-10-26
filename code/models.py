from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()
engine = create_engine('sqlite:///data/db.db?check_same_thread=False')
new_session = sessionmaker(engine)


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    telegram_id = Column(Integer)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f'<User @{self.username} ({self.telegram_id})>'


class Sport(Base):
    __tablename__ = 'sport'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    title = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f'<Sport {self.title}>'


class Event(Base):
    __tablename__ = 'event'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    sport_id = Column(Integer, ForeignKey('sport.id'))
    record = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f'<Event {self.id} ({self.record})>'


Base.metadata.create_all(engine)
