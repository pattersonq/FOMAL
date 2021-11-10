import logging
from re import sub
from typing import Set
from praw import reddit
import praw
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
from praw.models import MoreComments
from progress.bar import Bar
from pprint import pprint
from inspect import getmembers
from types import FunctionType
import pandas as pd
import coinmarketcapapi
import config
import os

PORT = int(os.environ.get('PORT', 5000))

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')

def top_ten_satoshi_bot(update, context):
    fomal = praw.Reddit(
    client_id = config.id,
    client_secret = config.token,
    user_agent = config.username
)
    cmc = coinmarketcapapi.CoinMarketCapAPI(config.cmc_token)
    data_id_map = cmc.cryptocurrency_map()
    cryptos_list_names = []
    cryptos_list_symbols = []

    pd_crypto = pd.DataFrame(data_id_map.data, columns = ['name','symbol'])

    for crypto in pd_crypto['name'].tolist():
        cryptos_list_names.append(crypto.replace(" ", "_"))

    for crypto in pd_crypto['symbol'].tolist():
        cryptos_list_symbols.append(crypto.replace(" ","_"))

    cryptos = []
    limit = 10
    words = []


    sum_comments = 0

    interesting_flairs = ['Moonshot (low market cap)  🚀', 'Big Cap Coin']
        
    for i, submission in enumerate(fomal.subreddit("SatoshiStreetBets").hot(limit=None)):
        if submission.link_flair_text not in interesting_flairs:
            continue
        if i==0: 
            continue
        print('sub: {number}'.format(number = i))
        for j, comment in enumerate(submission.comments):
            if isinstance(comment, MoreComments):
                continue
            words += comment.body.split()
        words += submission.selftext.split()
        
        print(j)
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

            elif(word in cryptos_list_symbols):
                if 'low' in submission.link_flair_text:
                    flair = 'Low Market Cap'
                else:
                    flair = 'High Market Cap'
                crypto_in = word + flair #Counter cannot hash lists
                cryptos.append(crypto_in.replace(" ", "_"))
            
                    
            
    print(sum_comments)

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

    top_ten_cryptos = sorted(cryptos_dict.items(), key=lambda x:-x[1])[:10]


    for key, value in top_ten_cryptos:
        print('{key}: {value}'.format(key=key, value=value))

    for key, value in top_ten_cryptos:
        update.message.reply_text('{key}: {value}'.format(key=key, value=value))


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(config.telegram_token, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("top_ten_satoshi", top_ten_satoshi_bot))
    dp.add_handler(CommandHandler("help", help))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook('https://fomal.herokuapp.com/' + config.heroku_token)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()