from sqlalchemy import create_engine
import psycopg2
import coinmarketcapapi
from .data.config import Config, Fomal_subs, Psql_cred
import pandas as pd
import sys
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
        self.is_connected = False
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

    def disconnect_db(self):
        try:
            self.is_connected = False
            self.cur.close()
        except (Exception, psycopg2.DatabaseError) as error_db:
                print(error_db)
        finally:
                if self.conn is not None:
                    self.conn.close()

    def is_empty_coins(self):
        sql = "select exists(select * from coins);"
        if self.is_connected:
            self.cur.execute(
                (sql)
            )
            foo =  self.cur.fetchone()
            return not foo[0]
        else:
            print("Worker no conectado a base de datos", file=sys.stderr)
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
    
    #Updates new data coming for mentions to give it back without calculating
    def insert_mentions(self, list, forum = 'SatoshiStreetBets'):
        '''inserts list of tuples (symbol, n_mentions, forum) and forum name as string'''
        if self.is_connected:
            for row in list:
                self.cur.execute("INSERT INTO mentions(symbol, n_mentions, forum) VALUES (%s, %s, %s);", 
                    (row[0], row[1], forum))
            self.conn.commit()
        else:
           print("Worker no conectado a base de datos", file=sys.stderr)
           return 
        
    def insert_coins(self):
        '''Populates coins table'''
        if self.is_connected:
            cmc = coinmarketcapapi.CoinMarketCapAPI(Config.cmc_token)
            data_id_map = cmc.cryptocurrency_map()
            pd_crypto = pd.DataFrame(data_id_map.data, columns = ['name','symbol'])
            pd_crypto.to_sql('coins', con = self.engine, if_exists='append', index=False)      
        else:
            print("Worker no conectado a base de datos", file=sys.stderr)
            return 

    def fetch_coins_db(self):
        '''returns names and symbols as pd.DataFrame'''
        
        if self.is_connected:
            self.cur.execute(
                ("SELECT name, symbol FROM coins;")
            )
            sql = self.cur.fetchall()
        else:
           print("Worker no conectado a base de datos", file=sys.stderr)
           return 
        
        coin_name = []
        coin_symbols = []
        for row in sql:
            coin_name.append(row[0])
            coin_symbols.append(row[1])
        
        return pd.DataFrame({'name': coin_name, 'symbol': coin_symbols})

    def select_db(self, sql):       
        if self.is_connected:
            self.cur.execute(sql)
            ret = self.cur.fetchall()
        else:
            print("Worker no conectado a base de datos", file=sys.stderr)
            return      
        return ret

        

