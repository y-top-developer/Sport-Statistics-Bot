import datetime
import pandas as pd

from models import Event, Sport, new_session, User
import orm
from settings import TELEGRAM_TOKEN, ADMINS, RECORD_FORMAT


def create_user(session, message):
    is_admin = False
    if message.from_user.username in ADMINS or message.chat.type == 'private':
        is_admin = True

    return orm.create_user(session, User(
        chat_id=message.chat.id,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        is_admin=is_admin
    ))


def events_to_df(events):
    events['event_created_at'] = events['event_created_at'].apply(
        lambda x: (x + datetime.timedelta(hours=3)).date())
    events['record_sum'] = events['record'].apply(
        lambda x: sum(list(map(int, x.split('-')))))
    df_groupby = events.groupby(['user_name', 'event_created_at']).sum()
    template = {datetime.datetime.now().date(
    ) - datetime.timedelta(days=i): 0 for i in range(3, -1, -1)}
    result = {name: template.copy()
              for (name, _) in df_groupby.record_sum.keys()}
    for (name, date), record_sum in df_groupby.record_sum.items():
        if date in template:
            result[name][date] = record_sum
    result_ = {'name': [], 'date': [], 'sum': []}
    for name, values in result.items():
        for date, sum_ in values.items():
            result_['name'].append(name)
            result_['date'].append(date.strftime('%d-%m-%y'))
            result_['sum'].append(sum_)

    return pd.DataFrame(result_)

def get_all_stats(session, chat_id):
    all_data = pd.DataFrame(orm.get_all_by_last_30_days(session, chat_id), columns=['user_name', 'sport_title', 'event_created_at', 'record'])
    current_monday = (datetime.datetime.now() - datetime.timedelta(days = datetime.datetime.now().weekday())).date()
    sports = {}
    for sport_title, sport_data in all_data.groupby('sport_title'):
        sport_data['record'] = sport_data['record'].apply(lambda x: sum(list(map(int, x.split('-')))))
        sport_data['event_created_at'] = sport_data['event_created_at'].apply(lambda x: (x + datetime.timedelta(hours=3)).date())
        sport_data = sport_data[sport_data['event_created_at'] >= current_monday]
        if sport_data['record'].sum() == 0:
            continue
        users = {i:0 for i in sport_data[sport_data['sport_title'] == sport_title]['user_name'].unique()}
        current_week = {current_monday + datetime.timedelta(days=i):users.copy() for i in range(0, 7)}
        for date, date_data in sport_data.groupby('event_created_at'):
            for user_name, user_name_data in date_data.groupby('user_name'):
                current_week[date][user_name] = user_name_data['record'].sum()
        result = {'name': [], 'date': [], 'sum': []}
        for date, values in current_week.items():
            for name, sum_ in values.items():
                result['name'].append(name)
                result['date'].append(date.strftime('%d-%m-%y'))
                result['sum'].append(sum_)
        sports[sport_title] = pd.DataFrame(result)
    return sports