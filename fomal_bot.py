import logging
from time import timezone
from praw import reddit
import praw
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
from praw.models import MoreComments
from praw.models.reddit.message import Message
from config import Config
import os
import datetime
import pytz
import pandas as pd
from database import Db_manager

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def top_ten_satoshi(context):
    fomal = praw.Reddit(
    client_id = Config.id,
    client_secret = Config.token,
    user_agent = Config.username
)

    context.bot.send_message(text='Analyzing... Give me 5-10 minutes, I am still slow AF', chat_id=context.job.context)

    # Connect database
    db = Db_manager()

    pd_crypto = pd.DataFrame(db.select_db(), columns=['names', 'symbols'])

    db.disconnect_db()
    
    cryptos_list_names = pd_crypto['names']

    for crypto in cryptos_list_names:
        crypto.replace(" ", "_")


    cryptos = []
    words = []
    i = 0
    j = 0

    sum_comments = 0

    interesting_flairs = ['Moonshot (low market cap)  🚀', 'Big Cap Coin']
        
    for i, submission in enumerate(fomal.subreddit("SatoshiStreetBets").hot(limit=None)):
        if submission.link_flair_text not in interesting_flairs:
            continue
        if i==0: 
            continue
        for j, comment in enumerate(submission.comments):
            if isinstance(comment, MoreComments):
                continue
            words += comment.body.split()
        words += submission.selftext.split()

        sum_comments += j

        cryptos = []
        for word in words:
            if word[0] == '$':
                word = word[1:]
            if(word in cryptos_list_names):
                if 'low' in submission.link_flair_text:
                    flair = 'Low Market Cap'
                else:
                    flair = 'Big Market Cap'
                crypto_in = word + flair
                cryptos.append(crypto.replace(" ", "_"))

            elif(word in pd_crypto['symbols']):
                if 'low' in submission.link_flair_text:
                    flair = 'Low Market Cap'
                else:
                    flair = 'High Market Cap'
                crypto_in = word + flair #Counter cannot hash lists
                cryptos.append(crypto_in.replace(" ", "_"))

    cryptos_dict = Counter(cryptos)
    new_dict = {}
    for key in cryptos_dict.keys():
        for sub_key in cryptos_dict.keys():
            if key is not sub_key:
                if sub_key in pd_crypto['symbol']:
                    if pd_crypto.set_index('name').at[sub_key, 'symbol'] in key:
                        value = cryptos_dict[key] + cryptos_dict[sub_key]
                        cryptos_dict.pop(sub_key, None)
                        new_dict.push({key: key,
                                value: value})

                elif sub_key in pd_crypto['name']:
                    if pd_crypto.set_index('symbol').at[sub_key, 'name'] in key:
                        value = cryptos_dict[key] + cryptos_dict[sub_key]
                        cryptos_dict.pop(sub_key, None)
                        new_dict.push({key: key,
                                value: value})
                        
    print(new_dict.keys, new_dict.values)
    top_ten_cryptos = sorted(new_dict.items(), key=lambda x:-x[1])[:10]

    message = ''

    for crypto, value in top_ten_cryptos:
        message += '{}: {}'.format(crypto, value)

    for key, value in top_ten_cryptos:
        print('{key}: {value}'.format(key=key, value=value))
        context.bot.send_message(chat_id=context.job.context ,text='{key}: {value}'.format(key=key, value=value))
    
    context.bot.send_message(chat_id=context.job.context ,text='{i} posts analyzed'.format(i=i))
    context.bot.send_message(chat_id=context.job.context ,text='{sum_comments} comments analyzed'.format(sum_comments=sum_comments))

    

def top_ten_satoshi_direct(update, context):
        context.job_queue.run_once(top_ten_satoshi, 0, context=update.message.chat_id)

def remove_job_if_exists(update, context) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.jobs()
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

def stupid_hello(context):
    job = context.job
    context.bot.send_message(chat_id=job.context ,text='Hello World')


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def set_timer(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    if len(context.args) != 3:
        update.message.reply_text('You need to introduce 3 numbers, interval, start_hour, finish_hour')
        update.message.reply_text('For example: /set_timer 30 9 22')
        update.message.reply_text('Would call the bot every 30 minutes, from 9 to 22 hours')
        return
    
    for i in range(2):
        if int(context.args[i]) <= 0:
            update.message.reply_text('We do not support going back in time, yet')
            update.message.reply_text('Try with positive numbers')
            return
    if int(context.args[1]) >= int(context.args[2]):
        update.message.reply_text('The starting hour goes before the finish hour: interval start finish')
        update.message.reply_text('If you meant it that way... not implemented yet')

    if not 1 <= int(context.args[0]) <= 1440:
        update.message.reply_text('Interval not valid')
        return
    for i in range(2)[1:]:
        if not 0 <= int(context.args[i]) <= 24:
            update.message.reply_text('Hour not valid, must be 0-24')
            return
    
    update.message.reply_text('Hi! setting timer')
    job_removed = remove_job_if_exists(update, context)
    
    now = datetime.datetime.now()
    now.replace(tzinfo=pytz.timezone('Europe/Madrid'))
    first = datetime.datetime(year=now.year, month=now.month,
                                day=now.day, hour=int(context.args[1]),
                                minute=0, second=0, tzinfo=now.tzinfo)
    last = datetime.datetime(year=now.year, month=now.month,
                                day=now.day, hour=int(context.args[2]),
                                minute=0, second=0, tzinfo=now.tzinfo)              

    if now.hour >= first.hour:
        update.message.reply_text('Not implemented yet, problems with timezones, start_hour must be later')
        return

    chat_id = update.message.chat_id
    
    context.job_queue.run_repeating(top_ten_satoshi, interval = 60*int(context.args[0]),
                                    first=(3600*(first.hour-now.hour)-60*(now.minute)),
                                    last=(3600*(last.hour-now.hour)-60*(now.minute)),
                                    context=chat_id)
    #For debugging purposes only
    '''context.job_queue.run_repeating(stupid_hello, interval=int(context.args[0]), context=chat_id)'''
    '''context.job_queue.run_repeating(stupid_hello, interval = int(context.args[0]),
                                    first=(60*((now.minute-first.minute) if now.minute >= first.minute else (first.minute -now.minute))),
                                    last=(60*((now.minute-last.minute) if now.minute >= last.minute else (last.minute -now.minute))),
                                    context=chat_id)'''

    text = 'Timer successfully set! from {start} to {finish} every {mins} minutes'.format(start=int(context.args[1]), finish=int(context.args[2]), mins=int(context.args[0]))
    if job_removed:
        text += ' Old one was removed.'
    update.message.reply_text(text)

def start(update, context):
    update.message.reply_text('Hi!')

def unset(update: Update,context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    job_removed = remove_job_if_exists(update, context)
    text = 'Timer successfully cancelled!' if job_removed else 'You have no active timer'
    update.message.reply_text(text)

def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('/start, /set_timer, /unset')
    update.message.reply_text('For example: /set_timer 30 9 22')


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(Config.telegram_token, use_context=True)
    port = os.getenv('PORT', 8443)
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Connect database
    db = Db_manager()
    if db.is_empty:
        db.populate_db()
    db.disconnect_db

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("top_ten_satoshi", top_ten_satoshi_direct))
    dp.add_handler(CommandHandler("set_timer", set_timer, pass_job_queue=True))
    dp.add_handler(CommandHandler("unset", unset))
    dp.add_handler(CommandHandler("help", help))

    # log all errors
    dp.add_error_handler(error)

    # Start bot for local usasation
    '''updater.start_polling()'''

    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=port,
                          url_path=Config.heroku_token,
                          webhook_url='https://fomal.herokuapp.com/' + Config.heroku_token)


    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()