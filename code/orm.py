import datetime
from typing import List
from sqlalchemy.orm import Session

from models import Event, Sport, User


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


def get_sport(session: Session, title: str, chat_id: int) -> Sport:
    return (
        session.query(
            Sport
        )
        .filter(
            Sport.title == title,
            Sport.chat_id == chat_id
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
