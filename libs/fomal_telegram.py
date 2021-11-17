from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from .data.config import Config, Fomal_subs
from .fomal_bot_db import Db_looker
import os
import datetime
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def top(num : int, sub : str):
    '''Gets latest data from the db and sends the message to the user'''
    db = Db_looker()
    db.connect_db()

    num = int(num)

    if not sub in Fomal_subs.subs:
        ret = "At the moment only {} are supported".format(Fomal_subs.subs)
        return ret

    if num <= 0 or num > 100:
        ret = """I only can show you a top 1-100, 
                                    second argument must be between those values"""
        return ret

    if db.has_worked():   
        pd_mentions = db.fetch_top_db(forum = sub, top = num)           
            
    else:
        ret= "Data is not ready yet, try again in some minutes"
        return ret
        
    output = ''
    for index, row in pd_mentions.iterrows():
        output += '{symbol}: {mentions}\n'.format(symbol=row[0], mentions=row[1])

    db.disconnect_db()
    if len(output) == 0:
        ret= "Data is not ready yet, try again in some minutes"
        return ret
    return output

def top_set(context : CallbackContext):
    context.bot.send_message(top(context.args[3], context.args[4]),chat_id=context.job.context)

def top_one(update : Update, context : CallbackContext):
    if not len(context.args) == 2:
        update.message.reply_text("Only two parameters should be passed")
        return
    update.message.reply_text(top(context.args[0], context.args[1]))

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
    """Send a message when the command /set_timer is issued, order of args: interval, start, finish, top_num, sub."""
    if not len(context.args) == 5:
        update.message.reply_text('You need to introduce 5 arguments, interval, start_hour, finish_hour, top_num, Subreddit')
        update.message.reply_text('For example: /set_timer 30 9 22 10 SatoshiStreetBets')
        update.message.reply_text('Would call the bot every 30 minutes, from 9 to 22 hours, to give you a top_ten from SatoshiStreetBets')
        return
    interval = int(context.args)[0]
    start = int(context.args)[1]
    finish = int(context.args)[2]
    top_num = int(context.args)[3]
    sub =  context.args[4]
    
    for i in range(2):
        if int(context.args[i]) <= 0:
            update.message.reply_text('We do not support going back in time, yet')
            update.message.reply_text('Try with positive numbers')
            return

    if start == 24:
        start = 0
        
    if start >= finish:
        update.message.reply_text('The starting hour goes before the finish hour: interval start finish')
        update.message.reply_text('If you meant it that way... not implemented yet')
        return

    if not 1 <= interval <= 1440:
        update.message.reply_text('Interval not valid')
        return
    for i in range(2)[1:]:
        if not 0 <= int(context.args[i]) <= 24:
            update.message.reply_text('Hour not valid, must be 0-24')
            return
    if top_num <= 0 or top_num > 50:
        update.message.reply_text('Top_{} too much, only 0-50 available', top_num)
        return

    if sub not in Fomal_subs.subs:
        update.message.reply_text('Sorry we do not support {}, only {} are available at the moment', sub, Fomal_subs.subs)
        return

    update.message.reply_text('Hi! setting timer')
    job_removed = remove_job_if_exists(update, context)
    
    now = datetime.datetime.now()
    first = datetime.datetime(year=now.year, month=now.month,
                                day=now.day, hour=int(start),
                                minute=0, second=0, tzinfo=now.tzinfo)
    last = datetime.datetime(year=now.year, month=now.month,
                                day=now.day, hour=int(finish),
                                minute=0, second=0, tzinfo=now.tzinfo)              

    if now.hour >= first.hour:
        update.message.reply_text('Not implemented yet, problems with timezones, start_hour must be later')
        return
    
    #the magic numbers are because I am eluding the time zone problem for now
    context.job_queue.run_repeating(top_set, context=context, interval = 60*interval,
                                    first=(3600*(first.hour-now.hour)-60*(now.minute)),
                                    last=(3600*(last.hour-now.hour)-60*(now.minute)),
                                    )

    text = 'Timer successfully set! from {start} to {finish} every {mins} minutes'.format(start=start, finish=start, mins=interval)
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
    update.message.reply_text('/start, /top, /set_timer, /unset')
    update.message.reply_text('For example: /top 15 SatoshiStreetBets')
    update.message.reply_text("""Or /set_timer 30 9 22 10 CryptoCurrency 
    for getting every 30 minutes from 9 to 22 top_10 from CryptoCurrency""")



def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


class Fomal_telegram():
    def __init__(self, local=False):
        self.telegram_token = Config.telegram_token
        self.port = Config.port
        self.is_local = local

    def connect_telegram(self):
        updater = Updater(self.telegram_token, use_context=True)
        port = os.getenv('PORT', self.port)
        # Get the dispatcher to register handlers
        dp = updater.dispatcher
        # on different commands - answer in Telegram
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("top", top_one))
        dp.add_handler(CommandHandler("set_timer", set_timer, pass_job_queue=True))
        dp.add_handler(CommandHandler("unset", unset))
        dp.add_handler(CommandHandler("help", help))

        # log all errors
        dp.add_error_handler(error)
        if self.is_local:
            # Start bot for local usasage
            updater.start_polling()
        else:
            # Start the Bot
            updater.start_webhook(listen="0.0.0.0",
                                port=port,
                                url_path=Config.heroku_token,
                                webhook_url='https://fomal.herokuapp.com/' + Config.heroku_token)

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()