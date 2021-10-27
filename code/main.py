import os
import re
import telebot
import datetime
import matplotlib
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


from models import Event, Sport, new_session, User
from orm import create_sport, get_all_users, get_sport, get_user, add_event, get_events_by_sport, get_sports
from messages import create_user, events_to_df
from settings import TELEGRAM_TOKEN, RECORD_FORMAT

matplotlib.pyplot.switch_backend('Agg')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
session = new_session()
re_record = re.compile(RECORD_FORMAT)

@bot.message_handler(commands=['help'])
def help_(message):
    bot.send_message(message.chat.id, '''Hi, glad to see you!) 
I\'m a bot that allows you to track sports achievements in the chat

/reg_sport sport_name - add new sport [admin only/private chat]
/add record - add new entry for existing sport
/stats sport_name - get a plot for the last 4 days
/list - get a list of all sports
''')

@bot.message_handler(commands=['list'])
def list_(message):
    sports = get_sports(session, message.chat.id)
    if sports:
        sports = '\n'.join([f'- {i[0]}' for i in sports])
        bot.send_message(message.chat.id, sports)
    else:
        bot.send_message(message.chat.id, '[-] nothing found')

@bot.message_handler(commands=['reg_sport'])
def register_activity_(message):

    message_text = message.text.split()[1:]

    if len(message_text) != 1:
        bot.send_message(message.chat.id, '[-] /reg_sport sport_name')
        return

    user = create_user(session, message)
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

    user = create_user(session, message)

    event = add_event(session, Event(
        user_id=user.id,
        sport_id=sport.id,
        record=result
    ))

    if not event:
        bot.send_message(message.chat.id, f'[-] event does not created')
        return

    events = pd.DataFrame(get_events_by_sport(session, sport), columns=[
                          'user_name', 'event_created_at', 'record'])
    events_ = events.copy()
    events_['event_created_at'] = events_['event_created_at'].apply(
        lambda x: (x + datetime.timedelta(hours=3)).date())
    
    if set(events_.user_name) == set(events_.loc[events_['event_created_at'] == datetime.datetime.now().date()].user_name):
        result_df = events_to_df(events)

        plt.figure(figsize=(20, 10))
        plt.title(sport_name)
        sns.set_theme(style="darkgrid")
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

    result_df = events_to_df(events)

    plt.figure(figsize=(20, 10))
    plt.title(sport_name)
    sns.set_theme(style="darkgrid")
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
