import praw
from config import Config, Psql_cred
from database import Db_manager
from praw.models import MoreComments
from collections import Counter

def top_ten_satoshi_(db):
    '''Does the math'''
    fomal = praw.Reddit(
    client_id = Config.id,
    client_secret = Config.token,
    user_agent = Config.username
)    
    pd_crypto = db.get_data()
    
    for crypto in pd_crypto['name']:
        crypto.replace(" ", "_")


    cryptos = []
    words = []
    i = 0
    j = 0

    sum_comments = 0

    interesting_flairs = ['Moonshot (low market cap)  🚀', 'Big Cap Coin']
    '''sentiment=[] #lista con tuplas de cuenta de palabras bull, bear y coin 

    bull_keywords = ['up', 'rise', 'moon', 'rich', 'gem', 'bull', 'bullish', 'pump']
    bear_keywords = ['down', 'fall', 'dump', 'poor', 'bear']''' #still thinking about it
        
    for i, submission in enumerate(fomal.subreddit("SatoshiStreetBets").hot(limit=15)):
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
        
        for word in words:
            if word[0] == '$':
                word = word[1:]
            if(word in pd_crypto['name']):
                if 'low' in submission.link_flair_text:
                    flair = 'Low Market Cap'
                else:
                    flair = 'Big Market Cap'
                crypto_in = word + flair
                cryptos.append(crypto.replace(" ", "_"))

            elif(word in pd_crypto['symbol']):
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
                        
    top_ten_cryptos = sorted(new_dict.items(), key=lambda x:-x[1])[:10]
    return top_ten_cryptos
