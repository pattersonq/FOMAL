include config.mk

space := $(nullstring)

create_db:
	PGPASSWORD=$(PASSWORD) psql -h $(HOST) -U $(USER) $(DB) -f $(CREATE_FILE)

update_db:
	PGPASSWORD=$(PASSWORD) psql -h $(HOST) -U $(USER) $(DB) -f $(UPDATE_FILE)
	
clear_db:
	heroku pg:reset DATABASE

clear_mentions_db:
	PGPASSWORD=$(PASSWORD) psql -h $(HOST) -U $(USER) $(DB) -f $(CLEAR_FILE)

insert_db:
	PGPASSWORD=$(PASSWORD) psql -h $(HOST) -U $(USER) $(DB) -f $(INSERT_FILE)

run_bot:
	python3 fomal_bot.py True

run_worker:
	python3 fomal_work.py


