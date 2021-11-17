import pandas as pd
import psycopg2
from .data.config import Psql_cred, Fomal_subs
import pandas as pd
import sys

class Db_looker():
    def __init__(self) -> None:  
        self.conn = None
        self.cur = None
        self.db_name= Psql_cred.db_name
        self.user= Psql_cred.user
        self.password= Psql_cred.password
        self.host= Psql_cred.host
        self.port= Psql_cred.port
        self.is_connected = False

    def connect_db(self):
        if self.is_connected: 
            return
        try:
            self.conn = psycopg2.connect("dbname={db_name} user={user} password={password} host={host} port={port}".format(db_name=self.db_name, user=self.user, password=self.password, host=self.host, port=self.port))
            self.cur = self.conn.cursor()
        except (Exception, psycopg2.DatabaseError) as error_db:
                print(error_db)
        self.is_connected = True
    
    def disconnect_db(self):
        try:
            self.is_connected = False
            self.cur.close()
        except (Exception, psycopg2.DatabaseError) as error_db:
                print(error_db)
        finally:
                if self.conn is not None:
                    self.conn.close()

    def is_accesible(self):
        '''returns bool meaning if there are mentions'''
        if self.is_connected:
            sql = "SELECT exists (SELECT symbol FROM mentions)"
            if self.is_connected:
                self.cur.execute(sql)
                res = self.cur.fetchone()
                return res
        else:
            print("Bot no conectado a base de datos", file=sys.stderr)
            return

    def has_worked(self):
        '''Returns dict with key=sub, value=Bool'''
        work_dict = {}
        for sub in Fomal_subs.subs:
            sql = "select exists(select * from mentions where forum = '{}');".format(sub)
            if self.is_connected:
                self.cur.execute(
                    (sql)
                )
                foo =  self.cur.fetchone()[0]
            else:
                print("Worker no conectado a base de datos", file=sys.stderr)
                return
            work_dict[sub] = foo
        return work_dict

    def fetch_top_db(self, forum = 'SatoshiStreetBets', top = 10):
        '''returns names and mentions as pd.DataFrame, default forum is SSB and number of rows 10'''

        if self.is_connected:
            self.cur.execute(
                ("SELECT t.symbol, t.n_mentions FROM (SELECT symbol, n_mentions FROM mentions WHERE forum = %s ORDER BY last_mod DESC) AS t ORDER BY n_mentions DESC LIMIT %s;"),
                (forum, top)
            )
            sql = self.cur.fetchall()
            coin_name = []
            coin_mentions = []
            for row in sql:
                coin_name.append(row[0])
                coin_mentions.append(row[1])
            
            return pd.DataFrame({'name': coin_name, 'mentions': coin_mentions})
        else:
            print("Bot no conectado a base de datos", file=sys.stderr)
            return


    def select_db(self, sql):
        if self.is_connected:
            self.cur.execute(sql)
            ret = self.cur.fetchall()
            return ret
        else:
            print("Bot no conectado a base de datos", file=sys.stderr)
            return