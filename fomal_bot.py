import logging
import numpy as np
import matplotlib.pyplot as plt
from praw.models.reddit.message import Message
from sqlalchemy.sql.expression import update
from config import Config
import os
import datetime
from database import Db_manager
from forum import top_ten_satoshi_
import threading
import time
import io

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def top_ten_satoshi(update, context):
    '''Just gets the data from the db'''
    db = Db_manager()
    sql = "select exists(select * from information_schema.tables where table_name='{}')".format('top_ten_satoshi',)
    res = db.select_db(sql)[0][0]
    if not res:   
        symbols, mentions = db.fetch_db()           
            
    else:
        update.message.reply_text("Data is not ready yet, try again in some minutes")
        return

    output = io.StringIO()
    for symbol, mention in [symbols,mentions]:
        print('{symbol}: {mentions}'.format(symbol=symbol, mentions=mention), file=output)
    update.message.reply_text(output)
    output.close()

def remove_job_if_exists(update, context) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    curent_jobs = context.job_queue.jobs()
    if not curent_jobs:
        return False
    for job in curent_jobs:
        job.schedule_removal()
    return True

def stupid_hello(context):
    '''Debugging'''
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

def top_ten_satoshi_save(context):
    return top_ten_satoshi(context)
    

def set_global_timer(context, interval):
    context.jobqueue.run_repeating(top_ten_satoshi_save, 3600, 0, 3600*17)

def connect_telegram(db):
    updater = Updater(Config.telegram_token, use_context=True)
    port = os.getenv('PORT', 8443)
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("top_ten_satoshi", top_ten_satoshi))
    dp.add_handler(CommandHandler("set_timer", set_timer, pass_job_queue=True))
    dp.add_handler(CommandHandler("unset", unset))
    dp.add_handler(CommandHandler("help", help))

    # log all errors
    dp.add_error_handler(error)

    # Start bot for local usasation
    updater.start_polling()

    # Start the Bot
    '''updater.start_webhook(listen="0.0.0.0",
                          port=port,
                          url_path=Config.heroku_token,
                          webhook_url='https://fomal.herokuapp.com/' + Config.heroku_token)'''

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

def async_update(db):
    while(True):
        now = datetime.datetime.now()
        h_start = 7
        h_end = 24

        sql = "select exists(select * from information_schema.tables where table_name= '{}')".format('last_modified',)
        last_exist = db.select_db(sql)[0][0]

        if last_exist:
            sql = "SELECT last_date, last_time FROM last_modified"
            res = db.select_db(sql)
            last_date = datetime.date.fromisoformat(res[0][0])
            last_time = datetime.time.fromisoformat(res[1][0])
            last = datetime.datetime.combine(last_date, last_time)

            if not (datetime.datetime.now() - last).total_seconds() < 1800:
                db.modify_db(top_ten_satoshi_())
                time.sleep(3600)
            else:
                time.sleep(1800)
        else:
            res = top_ten_satoshi_(db)
            db.modify_db(res)
            print("Analisis acabado")
            time.sleep(3600)


def main():
    # Connect database
    db = Db_manager()
    db.create_table_coins()
    
    t_async = threading.Thread(target=async_update, args=[db])
    t_async.start()
    connect_telegram(db)
    t_async.join()
    

if __name__ == '__main__':
    main()