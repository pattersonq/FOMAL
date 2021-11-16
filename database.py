import datetime
from logging import config
from os import replace
from numpy import dtype
from numpy.lib.function_base import append
from pandas.core.indexes.base import Index
from pandas.io.sql import execute
import psycopg2
import coinmarketcapapi
from sqlalchemy.sql.sqltypes import DateTime, Integer
from config import Config, Psql_cred
import pandas as pd
import numpy as np
from psycopg2.extras import execute_values
import threading
from sqlalchemy import create_engine, Table, Column, MetaData, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


class Db_manager():

    def __init__(self) -> None:  
        self.conn = None
        self.cur = None
        self.engine = create_engine(Psql_cred.uri, echo=False)
        self.db_name= Psql_cred.db_name
        self.user= Psql_cred.user
        self.password= Psql_cred.password
        self.host= Psql_cred.host
        self.port= Psql_cred.port
        self.sem_db = threading.BoundedSemaphore(value=4)
        self.is_connected = False
        self.lock = threading.RLock()
        self.is_empty = False

    def connect_db(self):
        if self.is_connected: 
            return
        try:
            self.conn = psycopg2.connect("dbname={db_name} user={user} password={password} host={host} port={port}".format(db_name=self.db_name, user=self.user, password=self.password, host=self.host, port=self.port))
            self.cur = self.conn.cursor()
        except (Exception, psycopg2.DatabaseError) as error_db:
                print(error_db)
        self.is_connected = True

    def insert_coins(self):
        cmc = coinmarketcapapi.CoinMarketCapAPI(Config.cmc_token)
        data_id_map = cmc.cryptocurrency_map()

        pd_crypto = pd.DataFrame(data_id_map.data, columns = ['name','symbol'])
        
        self.sem_db.acquire()
        self.connect_db()
        pd_crypto.to_sql('coins', con = self.engine, if_exists='append', index=False)
        self.sem_db.release()
        self.disconnect_db()

    def is_empty_check(self):
        sql = "select exists(select * from coins);"
        self.sem_db.acquire()
        self.connect_db()
        self.cur.execute(
            (sql)
        )
        foo =  self.cur.fetchone()
        self.disconnect_db()
        self.sem_db.release()
        return not foo[0]

    def has_worked(self):
        sql = "select exists(select * from top_ten_satoshi);"
        self.sem_db.acquire()
        self.connect_db()
        self.cur.execute(
            (sql)
        )
        foo =  self.cur.fetchone()[0]
        self.disconnect_db()
        self.sem_db.release()
        return foo

    def disconnect_db(self):
        try:
            self.is_connected = False
            self.cur.close()
        except (Exception, psycopg2.DatabaseError) as error_db:
                print(error_db)
        finally:
                if self.conn is not None:
                    self.conn.close()
    
    #Updates new data coming for mentions to give it back without calculating
    def insert_top_ten(self, list):
        '''Hay que cambiarla para que no solo modifique satoshi, list es lista de duplas'''
        "INSERT INTO top_ten_satoshi(symbol, mentions) VALUES (%s, %s ,%s)"
        
        self.lock.acquire()
        self.connect_db()
        for row in list:
            self.cur.execute("INSERT INTO top_ten_satoshi(symbol, mentions) VALUES (%s, %s);", 
                (row[0], row[1]))
        self.conn.commit()
        self.disconnect_db()
        self.lock.release()

    def fetch_db(self):
        '''returns names and symbols as pd.DataFrame'''

        self.lock.acquire()
        self.connect_db()
        self.cur.execute(
            ("SELECT name, symbol FROM coins;")
        )
        sql = self.cur.fetchall()
        self.disconnect_db()
        self.lock.release()
        coin_name = []
        coin_symbols = []
        for row in sql:
            coin_name.append(row[0])
            coin_symbols.append(row[1])
        
        return pd.DataFrame({'name': coin_name, 'symbol': coin_symbols})


    def fetch_top_ten_db(self):
        '''returns names and mentions as pd.DataFrame'''

        self.lock.acquire()
        self.connect_db()
        self.cur.execute(
            ("SELECT symbol, mentions FROM top_ten_satoshi ORDER BY last_mod DESC LIMIT 10;")
        )
        sql = self.cur.fetchall()
        self.disconnect_db()
        self.lock.release()
        coin_name = []
        coin_mentions = []
        for row in sql:
            coin_name.append(row[0])
            coin_mentions.append(row[1])
        
        return pd.DataFrame({'name': coin_name, 'mentions': coin_mentions})

    def select_db(self, sql):
        self.lock.acquire()
        self.connect_db()
        self.cur.execute(sql)
        ret = self.cur.fetchall()
        self.disconnect_db()
        self.lock.release()
        return ret

        

