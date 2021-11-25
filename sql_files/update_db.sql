--For changes in db without need to reset--
CREATE OR REPLACE FUNCTION fill_coin_id() returns trigger AS $$
BEGIN 
    UPDATE mentions
    SET new.coin_id = coins.coin_id
    WHERE new.symbol = coins.symbol;
END;
$$
language 'plpgsql';

DROP TRIGGER IF EXISTS coin_id_trigger ON mentions;

CREATE TRIGGER coin_id_trigger 
AFTER INSERT on mentions
FOR EACH ROW EXECUTE PROCEDURE fill_coin_id();