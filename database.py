import datetime
from logging import config
from os import replace
from numpy import dtype
from numpy.lib.function_base import append
from pandas.core.indexes.base import Index
import psycopg2
import coinmarketcapapi
from config import Config, Psql_cred
import pandas as pd
import numpy as np
from psycopg2.extras import execute_values
import threading
from sqlalchemy import create_engine, Table, Column, MetaData, Date, Time


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

    def connect_db(self):
        if self.is_connected: 
            return
        try:
            self.conn = psycopg2.connect("dbname={db_name} user={user} password={password} host={host} port={port}".format(db_name=self.db_name, user=self.user, password=self.password, host=self.host, port=self.port))
            self.cur = self.conn.cursor()
        except (Exception, psycopg2.DatabaseError) as error_db:
                print(error_db)
        self.is_connected = True

    def create_table_coins(self):
        cmc = coinmarketcapapi.CoinMarketCapAPI(Config.cmc_token)
        data_id_map = cmc.cryptocurrency_map()

        pd_crypto = pd.DataFrame(data_id_map.data, columns = ['name','symbol'])
        with self.sem_db:
            try:
                self.connect_db()
                pd_crypto.to_sql('coins', con = self.engine, if_exists='replace')
            finally:
                self.disconnect_db()

    def is_empty(self):
        with self.sem_db:
            try:
                self.connect_db()
                self.cur.execute(
                    ("SELECT * FROM coins")
                )
            finally:
                self.disconnect_db()
        foo =  self.cur.fetchone()
        return not foo

    def disconnect_db(self):
        try:
            self.is_connected = False
            self.cur.close()
        except (Exception, psycopg2.DatabaseError) as error_db:
                print(error_db)
        finally:
                if self.conn is not None:
                    self.conn.close()
    #cambiar
    def get_data(self):
        '''returns names and symbols as pd.dataframe'''
        with self.sem_db:
            try:
                self.connect_db()
                sql = "SELECT name, symbol FROM coins"
                pd_dataframe = pd.read_sql(sql,con=self.engine)
            finally:
                self.disconnect_db()
        
        return pd_dataframe
    
    #Updates new data coming for mentions to give it back without calculating
    def modify_db(self, dict):
        '''Hay que cambiarla para que no solo modifique esto'''
        pd_coins = pd.DataFrame.from_dict(dict, dtype = str, orient='index', columns = ['symbol', 'mentions'])
        self.lock.acquire()
        self.connect_db()
        self.cur.execute("select exists(select * from information_schema.tables where table_name=%s)", ('last_modified',))
        last_exist = self.cur.fetchone()[0]
        self.lock.release()
        if not last_exist:
            meta = MetaData()
            last_modified = Table(
                'last_modified', meta,
                Column('last_date', Date),
                Column('last_time', Time)
            )
            now = datetime.datetime.now()
            hora = datetime.time(hour=now.hour,minute=now.minute,second=now.second)
            sql = "INSERT INTO last_modified(last_date, last_time) VALUES ({}, {});".format(datetime.date.today().strftime("'%Y-%m-%d'"), hora.strftime("'%H:%M:%S'"))
            self.lock.acquire()
            self.connect_db()
            pd_coins.to_sql('top_ten_satoshi', con = self.engine, if_exists='replace')
            meta.create_all(self.engine)
            self.cur.execute(sql)
            self.disconnect_db()
            self.lock.release()
        
        else:
            sql="UPDATE last_modified SET last = CURRENT_DATE;"
            self.lock.acquire()
            self.connect_db()
            pd_coins.to_sql('top_ten_satoshi', con = self.engine, if_exists='replace')
            self.cur.execute(sql)
            self.disconnect_db()
            self.lock.release()

        

    def fetch_db(self):
        '''returns names and mentions as lists'''

        self.lock.acquire()
        self.connect_db()
        self.cur.execute(
            ("SELECT symbol, mentions FROM top_ten_satoshi")
        )
        sql = self.cur.fetchall()
        self.disconnect_db()
        self.lock.acquire()

        pd_dataframe = pd.read_sql(sql,con=self.engine)
        pd_dataframe.columns = ['name', 'symbol']
        
        return pd_dataframe['name'], pd_dataframe['symbol']

    def select_db(self, sql):
        self.lock.acquire()
        self.connect_db()
        self.cur.execute(sql)
        ret = self.cur.fetchall()
        self.disconnect_db()
        self.lock.release()
        return ret

        

