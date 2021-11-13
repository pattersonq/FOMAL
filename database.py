import psycopg2
import coinmarketcapapi
from config import Config, Psql_cred
import pandas as pd
import re
from psycopg2.extras import execute_values

class Db_manager():

    def __init__(self) -> None:  
        conn = None
        curr = None
        db_name= Psql_cred.db_name
        user= Psql_cred.user
        password= Psql_cred.password
        host= Psql_cred.host
        port= Psql_cred.port
        #connect database
        try:
            self.conn = psycopg2.connect("dbname={db_name} user={user} password={password} host={host} port={port}".format(db_name=db_name, user=user, password=password, host=host, port=port))
            self.cur = self.conn.cursor()

        except (Exception, psycopg2.DatabaseError) as error_db:
                print(error_db)
        try:
            self.cur.execute(
                ("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'coins');")
            )
            foo = self.cur.fetchone()
            print(foo)
            if not foo[0]:
                self.cur.execute(
                ("CREATE TABLE coins(symbol varchar(40), coin_name varchar(100));")
            )
        except (Exception, psycopg2.DatabaseError) as error_db:
                print(error_db)
    def is_empty(self):
        self.cur.execute(
            ("SELECT * FROM coins")
        )
        foo =  self.cur.fetchone()
        return not foo

    def disconnect_db(self):
        try:
            self.cur.close()
        except (Exception, psycopg2.DatabaseError) as error_db:
                print(error_db)
        finally:
                if self.conn is not None:
                    self.conn.close()


    def populate_db(self):
        cmc = coinmarketcapapi.CoinMarketCapAPI(Config.cmc_token)
        data_id_map = cmc.cryptocurrency_map()
        cryptos_list_names = []
        cryptos_list_symbols = []

        pd_crypto = pd.DataFrame(data_id_map.data, columns = ['name','symbol'])

        #solo acepta aquellas que empiezan por letra y tan solo contienen letras y numeros
        pattern = re.compile(r'^[A-Za-z]+[0-9]*[A-Z]*[a-z]*$')
        cryptos_dict = pd_crypto.to_dict(orient='list')
        values_list = []
        sql = "INSERT INTO coins(symbol, coin_name) VALUES %s"
        for crypto in pd_crypto.itertuples():
            values = (getattr(crypto, 'symbol'), getattr(crypto, 'name'))
            values_list.append(values)

        execute_values(self.cur, sql, values_list)
        '''
        args_str = ','.join(self.cur.mogrify("(%s,%s)",symbol,name) for symbol,name in pd_crypto)
        self.is_populated = True'''
    
    def select_db(self):
        '''returns names and symbols as list'''
        self.cur.execute(
            ("SELECT name FROM coins")
        )
        names = self.cur.fetchall().split(",")
        self.cur.execute(
            ("SELECT symbol FROM coins")
        )
        symbols = self.cur.fetchall().split(",")

        return names, symbols
        
        