import os

RECORD_FORMAT = r'(\d+-)*\d+'

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
ADMINS = os.environ['ADMINS'].split(' ')