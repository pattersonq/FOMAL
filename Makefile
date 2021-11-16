include config.mk

space := $(nullstring)

create_db:
	PGPASSWORD=$(PASSWORD) psql -h $(HOST) -U $(USER) $(DB) -f $(CREATE_FILE)
	
clear_db:
	heroku pg:reset DATABASE

run:
	python3 fomal_bot.py

