from praw.models.reddit.message import Message
from praw.reddit import Subreddit
from sqlalchemy.sql.expression import update
import signal
import datetime
from libs.fomal_work_db import Db_manager
from libs.fomal_forum import analyze_hour
import threading
import time
from queue import PriorityQueue
from libs.data.config import Fomal_subs

lock_db = threading.Lock()

def signal_handler():
    global keep
    keep = True

def async_work(db, sub):
    start = datetime.datetime.now()
    print("Analisis empezado de {} a: {}".format(sub, start))
    lock_db.acquire()
    coins = db.fetch_coins_db()
    lock_db.release()
    mentions = analyze_hour(coins, sub)
    lock_db.acquire()
    db.insert_mentions(mentions, sub)
    lock_db.release()
    finish = datetime.datetime.now()
    print("Analisis finalizado de {} a {}".format(sub, finish))


def async_update(db : Db_manager, subs : str, queue : PriorityQueue):
    global keep
    while(keep):
        while(db.is_empty):
            time.sleep(5)
        lock_db.acquire()
        work_dict = db.has_worked()
        lock_db.release()
        subs_work = []
        subs_not_work = []
        subs_to_analyze = [] #the ones who have alreay worked but are outdated
        for sub in subs:
            if work_dict[sub]:
                subs_work.append(sub)
            else:
                subs_not_work.append(sub)
        if subs_work:
            for sub in subs_work:
                sql = "SELECT last_mod FROM mentions WHERE forum = '{}' ORDER BY last_mod DESC LIMIT 1".format(sub)
                lock_db.acquire()
                res = db.select_db(sql)[0][0]
                lock_db.release()
                tz = res.tzinfo
                now = datetime.datetime.now(tz=tz)
                if not (now - res).total_seconds() < 1800:
                    subs_to_analyze.append(sub)
        threads_to_join = []
        now = datetime.datetime.now()
        for sub in subs_not_work + subs_to_analyze:
            worker = threading.Thread(target=async_work, args=[db, sub], name=sub)
            threads_to_join.append(worker)
            worker.start()
        for thread in threads_to_join:
            thread.join()
        time_exec = now - datetime.datetime.now()
        time.sleep(3600 - time_exec.total_seconds())
            
def main():
    #Set SIGALRM handler
    signal.signal(signal.SIGALRM, signal_handler)

    # Connect database
    db = Db_manager()
    db.connect_db()

    #trabajo: mirar hace cuanto se actualizo
    if db.is_empty_coins():
        print("Insertando Datos")
        db.insert_coins()
        print("Datos insertados")

    subs = Fomal_subs.subs
    threads_queue = PriorityQueue(len(subs)) # Por si se quiere dar más prioridad a unos subs que a otros
    global keep
    keep = True
    async_update(db, subs, threads_queue)

    db.disconnect_db()
    

if __name__ == '__main__':
    main()