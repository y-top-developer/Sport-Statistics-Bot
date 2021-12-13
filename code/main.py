import os
import re
import random
import telebot
import datetime
import schedule 
import matplotlib
import pandas as pd
import seaborn as sns
from time import sleep
from threading import Thread
import matplotlib.pyplot as plt

from models import Chat, Event, Sport, new_session, User
from orm import remove_chat, get_chat, create_sport, get_sport, get_all_scheduled_chats, add_event, get_events_by_sport, get_sports, create_chat
from messages import create_user, events_to_df, get_all_stats
from settings import TELEGRAM_TOKEN, RECORD_FORMAT

matplotlib.pyplot.switch_backend('Agg')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
session = new_session()
re_record = re.compile(RECORD_FORMAT)
chats = re.compile(RECORD_FORMAT)

@bot.message_handler(commands=['help', 'start'])
def help_(message):
    bot.send_message(message.chat.id, '''Hi, glad to see you!) 
I\'m a bot that allows you to track sports achievements in the chat

/reg_chat - add chat to scheduler [admin only/private chat]
/remove_chat - remove chat from scheduler [admin only/private chat]
/reg_sport sport_name - add new sport [admin only/private chat]
/add sport_name record - add new entry for existing sport
/stats sport_name - get a plot for the last 4 days
/all_stats - get plots with sport results for the current week
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
    user_info = bot.get_chat_member(message.chat.id, message.from_user.id)
    if (not user or not (user.is_admin or user_info.status in ['creator', 'administrator'])):
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
    
    if set(events_.user_name) == set(events_.loc[events_['event_created_at'] == datetime.datetime.now().date()].user_name) and len(set(events_.user_name)) > 3:
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

def all_stats(message_chat_id):
    try:
        sports = get_all_stats(session, message_chat_id)
        files = []
        for i, (sport_title, result) in enumerate(sports.items()):
            plt.figure(figsize=(20, 10))
            plt.title(sport_title)
            sns.set_theme(style="darkgrid")
            sns.lineplot(x="date", y="sum", hue="name", data=result)
            for name, date, sum_ in result.values:
                plt.annotate(sum_, (date, sum_))
            plt.legend()
            filename = f'plot_{i}_{message_chat_id}.png'
            files.append(filename)
            plt.savefig(filename)
            plt.clf()
            plt.cla()
            plt.close()
        bot.send_media_group(message_chat_id, [telebot.types.InputMediaPhoto(open(photo, 'rb')) for photo in files])
        for filename in files:
            os.remove(filename)
    except Exception as e:
        bot.send_message(message_chat_id, f'[-] Can\'t get statistics')
        print(e)


@bot.message_handler(commands=['all_stats'])
def all_stats_wrapper(message):
    all_stats(message.chat.id)

@bot.message_handler(commands=['remove_chat'])
def remove_chat_wrapper(message):
    user = create_user(session, message)
    user_info = bot.get_chat_member(message.chat.id, message.from_user.id)
    if (not user or not (user.is_admin or user_info.status in ['creator', 'administrator'])):
        bot.send_message(
            message.chat.id, f'[-] {message.from_user.username} is not in the sudoers file. This incident will be reported')
        return

    if not get_chat(session, message.chat.id):
        bot.send_message(message.chat.id, f'[-] Сhat was not scheduled')
        return
    remove_chat(session, message.chat.id)
    if get_chat(session, message.chat.id):
        bot.send_message(message.chat.id, f'[-] Сhat not deleted')
    else:
        bot.send_message(message.chat.id, f'[+] Сhat deleted')

@bot.message_handler(commands=['reg_chat'])
def register_chat(message):
    message_text = message.text.split()[1:]

    if len(message_text) != 0:
        bot.send_message(message.chat.id, '[-] /reg_chat')
        return

    user = create_user(session, message)
    user_info = bot.get_chat_member(message.chat.id, message.from_user.id)
    if (not user or not (user.is_admin or user_info.status in ['creator', 'administrator'])):
        bot.send_message(
            message.chat.id, f'[-] {message.from_user.username} is not in the sudoers file. This incident will be reported')
        return

    if get_chat(session, message.chat.id):
        bot.send_message(message.chat.id, f'[-] Chat already scheduled')
        return

    create_chat(session, Chat(
        chat_id=message.chat.id,
        scheduled=True
    ))

    bot.send_message(message.chat.id, f'[+] Chat scheduled')
    

def schedule_checker():
    try:
        while True:
            schedule.run_pending()
            sleep(1)
    except Exception as e: 
        print(e)

def all_stats_schedule():
    quotes = [
        'When you’re riding, only the race in which you’re riding is important🐺',
        'Age is no barrier. It’s a limitation you put on your mind🐺',
        'One man practicing sportsmanship is far better than 50 preaching it🐺',
        'It’s not the will to win that matters—everyone has that. It’s the will to prepare to win that matters🐺',
        'Persistence can change failure into extraordinary achievement🐺',
        'If you can’t outplay them, outwork them🐺',
        'Most people never run far enough on their first wind to find out they’ve got a second🐺',
        'The difference between the impossible and the possible lies in a person’s determination🐺',
        'Champions keep playing until they get it right🐺',
        'Persistence can change failure into extraordinary achievement🐺',
        'The more difficult the victory, the greater the happiness in winning🐺'

    ]
    for chat in get_all_scheduled_chats(session):
        try:
            if datetime.date.today().weekday() == 0:
                sports = get_sports(session, str(chat[0]))
                if sports:
                    sports = '\n'.join(['Congratulations on Monday, it\'s time to train. Choose any sport or create new one\n'] + [f'- {i[0]}' for i in sports])
                    bot.send_message(str(chat[0]), sports)
                else:
                    bot.send_message(str(chat[0]), 'Congratulations on Monday, it\'s time to train. Create a sport')
            bot.send_message(str(chat[0]), random.choice(quotes))
            all_stats(str(chat[0]))
        except:
            try:
                bot.send_message(str(chat[0]), '[-] Can\'t send week statistics')
            except Exception as e:
                print(e)
            

if __name__ == "__main__":
    schedule.every().day.at('12:00').do(all_stats_schedule)
    Thread(target=schedule_checker).start() 
    bot.polling()
