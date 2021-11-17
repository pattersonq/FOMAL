import getopt
import numpy as np
import matplotlib.pyplot as plt
from praw.models.reddit.message import Message
from praw.reddit import Subreddit
from sqlalchemy.sql.expression import update
from libs.data.config import Fomal_subs
import sys
import datetime
from libs.fomal_work_db import Db_manager
from libs.fomal_bot_db import Db_looker
from libs.fomal_forum import analyze_hour
import threading
import time
from libs.fomal_telegram import Fomal_telegram
            
def main():
    # Connect database
    db = Db_looker()
    db.connect_db()

    #wait until worker has done something
    if not db.is_accesible():
        time.sleep(10)
    
    if len(sys.argv) == 2:
        tele = Fomal_telegram(local=True)
    else:
        tele = Fomal_telegram()

    tele.connect_telegram()

    db.disconnect_db()
    

if __name__ == '__main__':
    main()