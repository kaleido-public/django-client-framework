.EXPORT_ALL_VARIABLES:
PYTHONPATH="./:../"

default: reset
	poetry run coverage run --branch --source=../django_client_framework ./manage.py test --no-input -v2 -p "*.py"
	poetry run coverage xml

.PHONY: ci
ci: alpine-base
	docker-compose run --rm unit-tests-ci bash -c " \
		./manage.py makemigrations &&\
		./manage.py test --no-input -v2 -p '*.py' \
	"

.PHONY: alpine-base
alpine-base:
	docker-compose build unit-tests-ci

.PHONY: sh
sh: alpine-base
	docker-compose run --rm unit-tests-ci sh

.PHONY: reset
reset:
	-cd dcf_test_app/migrations && rm -f 0001_initial.py
	poetry run ./manage.py makemigrations

.PHONY: Makefile
Makefile:
	@echo

target debug: argv = $(subst ., ,$(MAKECMDGOALS))
target debug: module = $(word 2, $(argv))
target debug: method = $(word 3, $(argv))
debug:
	poetry run python -m debugpy --listen 5678 --wait-for-client ./manage.py test --no-input -v2 -p "$(module).py" -k "$(method)"

target debugmode: argv = $(subst ., ,$(MAKECMDGOALS))
target debugmode: module = $(word 2, $(argv))
target debugmode: method = $(word 3, $(argv))
debugmode:
	poetry run coverage run --branch --source=../django_client_framework ./manage.py test --debug-mode --no-input -v2 -p "$(module).py" -k "$(method)"
	poetry run coverage xml

target %: argv = $(subst ., ,$@)
target %: module = $(word 1, $(argv))
target %: method = $(word 2, $(argv))
%:
	poetry run coverage run --branch --source=../django_client_framework ./manage.py test --no-input -v2 -p "$(module).py" -k "$(method)"
	poetry run coverage xml
