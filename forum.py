import praw
from config import Config, Psql_cred
from database import Db_manager
from praw.models import MoreComments
from collections import Counter

def top_ten_satoshi_(pd_crypto):
    '''Does the math'''
    fomal = praw.Reddit(
    client_id = Config.id,
    client_secret = Config.token,
    user_agent = Config.username
)    

    cryptos = []
    j = 0
    z = 0

    sum_comments = 0

    common_words = ['the', 'THE', 'gas','GAS', 'hodl', 'HODL', 'fees', 'FEES', 'rise', 'RISE']
        
    for i, submission in enumerate(fomal.subreddit("SatoshiStreetBets").top("day", limit=10)):
        words = []
        if z == 2:
            break
        for j, comment in enumerate(submission.comments):
            if isinstance(comment, MoreComments):
                continue
            words += comment.body.split()
        words += submission.selftext.split()

        sum_comments += j
        
        for word in words:
            if z == 2:
                break
            if word[0] == '$':
                word = word[1:]
                for index, row in pd_crypto.iterrows():
                    if row['symbol'] == word:
                        cryptos.append(row['symbol'])
            else:
                for index, row in pd_crypto.iterrows():
                    #hay simbolos en mayusculas y en minusculas
                    if (row['name'] == word or row['symbol'] == word) and (not word in common_words):
                        cryptos.append(row['symbol'])
                        z+=1
                        if z == 2:
                            break

    cryptos_dict = Counter(cryptos)
    '''new_dict = {}'''
    #look for duplicated name and symbol being same coin
    '''for key in cryptos_dict.keys():
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
                                value: value})'''
    top_ten_cryptos = sorted(cryptos_dict.items(), key=lambda x:-x[1])[:10]
    return top_ten_cryptos
