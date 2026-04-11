PYTHON ?= python3
MANAGE = $(PYTHON) manage.py

.PHONY: migrate makemigrations collectstatic createsuperuser bootstrap-roles check shell backup restore

migrate:
	$(MANAGE) migrate

makemigrations:
	$(MANAGE) makemigrations

collectstatic:
	$(MANAGE) collectstatic --noinput

createsuperuser:
	$(MANAGE) createsuperuser

check:
	$(MANAGE) check

shell:
	$(MANAGE) shell

bootstrap-roles:
	$(MANAGE) bootstrap_roles

backup:
	./scripts/backup_db.sh

restore:
	./scripts/restore_db.sh $(FILE)
