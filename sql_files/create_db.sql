DROP TABLE IF EXISTS coins;
DROP TABLE IF EXISTS top_ten_satoshi;

CREATE OR REPLACE FUNCTION fill_coin_id() returns trigger AS $$
BEGIN 
    UPDATE mentions
    SET new.coin_id = coins.coin_id
    FROM coins
    WHERE new.symbol = coins.symbol;
END;
$$
language 'plpgsql';

DROP TRIGGER IF EXISTS coin_id_trigger ON mentions;

CREATE TABLE coins(
    coin_id INT GENERATED ALWAYS AS IDENTITY,
    symbol varchar(30),
    name varchar(60),
    PRIMARY KEY(coin_id)
);

CREATE TABLE mentions(
    coin_id int,
    symbol varchar(30),
    n_mentions int,
    forum varchar(60),
    last_mod TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT coin_mentioned FOREIGN KEY(coin_id) REFERENCES coins(coin_id) ON DELETE CASCADE
);

CREATE TRIGGER coin_id_trigger 
BEFORE INSERT on mentions
FOR EACH ROW 
EXECUTE PROCEDURE fill_coin_id();