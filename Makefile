include config.mk

space := $(nullstring)

create_db:
	psql -h $(HOST) -U $(USER) $(DB) -f $(CREATE_FILE)