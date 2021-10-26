import os
import re
import telebot
import datetime
import matplotlib
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


from models import Event, Sport, new_session, User
from orm import create_sport, create_user, get_all_users, get_sport, get_user, add_event, get_events_by_sport
from settings import TELEGRAM_TOKEN, ADMINS, RECORD_FORMAT

matplotlib.pyplot.switch_backend('Agg')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
session = new_session()
re_record = re.compile(RECORD_FORMAT)


@bot.message_handler(commands=['reg_me'])
def register_user(message):
    if message.from_user.username in ADMINS:
        create_user(session, User(
            chat_id=message.chat.id,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            is_admin=True
        ))
    else:
        bot.send_message(
            message.chat.id, f'[-] {message.from_user.username} is not in the sudoers file. This incident will be reported')


@bot.message_handler(commands=['reg_sport'])
def register_activity_(message):
    message_text = message.text.split()[1:]

    if len(message_text) != 1:
        bot.send_message(message.chat.id, '[-] /reg_sport sport_name')
        return

    user = get_user(session, message.from_user.id, message.chat.id)
    if not user or not user.is_admin:
        bot.send_message(
            message.chat.id, f'[-] {message.from_user.username} is not in the sudoers file. This incident will be reported')
        return

    sport_name = message_text[0]

    if get_sport(session, sport_name, message.chat.id):
        bot.send_message(message.chat.id, f'[-] {sport_name} already exist')
        return

    sport = create_sport(session, Sport(
        chat_id=message.chat.id,
        title=sport_name
    ))

    bot.send_message(message.chat.id, f'[+] Sport {sport.title} added')


@bot.message_handler(commands=['add'])
def add_event_(message):
    message_text = message.text.split()[1:]
    if len(message_text) != 2:
        bot.send_message(message.chat.id, '/add sport_name result')
        return

    sport_name = message_text[0]
    result = message_text[1]

    sport = get_sport(session, sport_name, message.chat.id)
    if not sport:
        bot.send_message(message.chat.id, f'[-] {sport_name} does not exist')
        return

    if not re_record.fullmatch(result):
        bot.send_message(
            message.chat.id, f'[-] \'{result}\' does not match by {RECORD_FORMAT}')
        return

    user = create_user(session, User(
        chat_id=message.chat.id,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    ))

    event = add_event(session, Event(
        user_id=user.id,
        sport_id=sport.id,
        record=result
    ))

    if not event:
        bot.send_message(message.chat.id, f'[-] event does not created')
        return


@bot.message_handler(commands=['stats'])
def stats(message):
    message_text = message.text.split()[1:]

    if len(message_text) != 1:
        bot.send_message(message.chat.id, '/stats sport_name')
        return

    sport_name = message_text[0]
    sport = get_sport(session, sport_name, message.chat.id)
    if not sport:
        bot.send_message(message.chat.id, f'[-] {sport_name} does not exist')
        return

    events = pd.DataFrame(get_events_by_sport(session, sport), columns=[
                          'user_name', 'event_created_at', 'record'])

    if events.empty:
        bot.send_message(message.chat.id, f'[-] {sport_name} has not events')
        return

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

    plt.figure(figsize=(20, 10))
    plt.title(sport_name)
    sns.set_theme(style="darkgrid")

    result_df = pd.DataFrame(result_)

    sns.lineplot(x="date", y="sum", hue="name", data=result_df)
    for name, date, sum_ in result_df.values:
        plt.annotate(sum_, (date, sum_))
    plt.legend()
    plt.savefig('plot_name.png')
    bot.send_photo(message.chat.id, photo=open('plot_name.png', 'rb'))
    os.remove('plot_name.png')
    plt.clf()
    plt.cla()
    plt.close()


if __name__ == "__main__":
    bot.polling()
