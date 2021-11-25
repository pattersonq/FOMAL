import praw
from .data.config import Config
from praw.models import MoreComments
from collections import Counter
from english_words import english_words_set
import datetime
from datetime import datetime, timedelta

def submissionsWithinHour(fomal, sub):
    '''List of ids of submissions'''
    subreddit = fomal.subreddit(sub)

    submissionsLastHour = []
    for submission in subreddit.new(limit=None): 
        utcPostTime = submission.created
        submissionDate = datetime.utcfromtimestamp(utcPostTime)

        currentTime = datetime.utcnow()

        #How long ago it was posted.
        submissionDelta = (currentTime - submissionDate).total_seconds()
        
        if submissionDelta <= 3600:
            submissionsLastHour.append(submission.id)
        else:
            break
    
    return submissionsLastHour

def analyze_hour(pd_crypto, sub = "SatoshiStreetBets"):
    '''Does the math, returns list of duples(symbol, mentions)'''
    reddit = praw.Reddit(
    client_id = Config.id,
    client_secret = Config.token,
    user_agent = Config.username
)    
    i = 0
    j = 0
    sum_comments = 0
    sum_words = 0
    cryptos = []
    common_words = {'hodl','stake','dyor', 'fomo'}

    interesting = ['NEW-COIN', 'GENERAL-NEWS', 'SPECULATION', 'STRATEGY', 'STAKING', 'MINING', 'TECHNOLOGY']
    
    last_hour_subs = submissionsWithinHour(reddit, sub)

    for id in last_hour_subs:
        submission = reddit.submission(id = id)
        words = []
        i+=1
        if sub == 'CryptoCurrency':
            if  not submission.link_flair_text in interesting:
                continue
        for comment in submission.comments:
            j += 1
            if isinstance(comment, MoreComments):
                continue
            words += comment.body.split()
        words += submission.selftext.split()
        words += submission.title.split()
        sum_comments += j
        
        for word in words:
            sum_words += len(words)
            if word[0] == '$':
                word = word[1:]
                for index, row in pd_crypto.iterrows():
                    if row['symbol'] == word:
                        cryptos.append(row['symbol'])
            else:
                if word in english_words_set.union(common_words):
                    continue
                for index, row in pd_crypto.iterrows():
                    #hay simbolos en mayusculas y en minusculas
                    #quintana dice que minisculas en la db :)
                    if (row['name'].lower() == word.lower() \
                        or row['symbol'].lower() == word.lower()):
                        cryptos.append(row['symbol'])
    
    print('{}, comments: {}, posts: {}, words: {}'.format(sub, sum_comments, i, sum_words))

    cryptos_dict = Counter(cryptos)
    top_ten_cryptos = sorted(cryptos_dict.items(), key=lambda x:-x[1])[:10]
    return top_ten_cryptos
