import datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import delete
from sqlalchemy.sql.functions import user

from models import Event, Sport, User, Chat


def get_user(session: Session, telegram_id: int, chat_id: int) -> User:
    return (
        session.query(
            User
        )
        .filter(
            User.telegram_id == telegram_id,
            User.chat_id == chat_id
        )
        .first()
    )

def remove_chat(session: Session, chat_id: int):
    sql_query = delete(Chat).where(Chat.chat_id == chat_id)
    session.execute(sql_query)
    session.commit()

def get_sport(session: Session, title: str, chat_id: int) -> Sport:
    return (
        session.query(
            Sport
        )
        .filter(
            Sport.title == title,
            Sport.chat_id == chat_id,
        )
        .first()
    )

def get_sports(session: Session, chat_id: int) -> List:
    return (
        session.query(
            Sport.title
        )
        .filter(
            Sport.chat_id == chat_id
        )
        .all()
    )

def get_all_users(session: Session, chat_id: int) -> List:
    return (
        session.query(
            User.username
        )
        .filter(
            User.chat_id == chat_id
        )
        .all()
    )


def get_events_by_sport(session: Session, sport: Sport) -> List:
    return (
        session.query(
            User.username,
            Event.created_at,
            Event.record
        )
        .filter(
            Event.sport_id == sport.id,
            Event.created_at >= datetime.datetime.now() - datetime.timedelta(days=4)
        )
        .join(
            User,
            User.id == Event.user_id
        )
        .join(
            Sport,
            Sport.id == Event.sport_id
        )
        .all()
    )

def get_all_scheduled_chats(session: Session) -> List:
    return (
        session.query(
            Chat.chat_id
        )
        .filter(
            Chat.scheduled == True
        )
        .all()
    )

def get_chat(session: Session, chat_id: str) -> Chat:
    return (
        session.query(
            Chat.chat_id
        )
        .filter(
            Chat.chat_id == chat_id
        )
        .all()
    )

def get_all_by_last_30_days(session: Session, chat_id: str) -> List:
    return (
        session.query(
            User.username,
            Sport.title,
            Event.created_at,
            Event.record
        )
        .filter(
            User.chat_id ==  chat_id, 
            Event.created_at >= datetime.datetime.now() - datetime.timedelta(days=30)
        )
        .join(
            User,
            User.id == Event.user_id
        )
        .join(
            Sport,
            Sport.id == Event.sport_id
        )
        .all()
    )

def create_user(session: Session, user: User) -> User:
    existing_user = get_user(session, user.telegram_id, user.chat_id)

    if not existing_user:
        session.add(user)
        session.commit()

    return get_user(session, user.telegram_id, user.chat_id)


def create_sport(session: Session, sport: Sport) -> Sport:
    existing_sport = get_sport(session, sport.title, sport.chat_id)

    if not existing_sport:
        session.add(sport)
        session.commit()

    return get_sport(session, sport.title, sport.chat_id)

def create_chat(session: Session, chat: Chat):
    session.add(chat)
    session.commit()

def add_event(session: Session, event: Event) -> Event:
    existing_user = (
        session.query(
            User
        )
        .filter(
            User.id == event.user_id
        )
        .first()
    )
    existing_sport = (
        session.query(
            Sport
        ).filter(
            Sport.id == event.sport_id
        )
        .first()
    )

    if existing_user and existing_sport:
        session.add(event)
        session.commit()

    return (
        session.query(
            Event
        )
        .filter(
            Event.user_id == event.user_id,
            Event.sport_id == event.sport_id,
            Event.record == event.record
        )
        .order_by(
            Event.id.desc()
        )
        .first()
    )
