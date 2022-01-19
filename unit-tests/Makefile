default: reset
	PYTHONPATH="./:../" poetry run coverage run --branch --source=../django_client_framework ./manage.py test --no-input -v2 -p "*.py"
	poetry run coverage xml

.PHONY: ci
ci: alpine-base
	docker-compose run --rm unit-tests-ci ./manage.py test --no-input -v2 -p "*.py"

.PHONY: alpine-base
alpine-base:
	docker-compose build unit-tests-ci

.PHONY: sh
sh: alpine-base
	docker-compose run --rm unit-tests-ci sh

.PHONY: reset
reset:
	-cd dcf_test_app/migrations && rm -f 0001_initial.py
	PYTHONPATH="./:../" poetry run ./manage.py makemigrations

.PHONY: Makefile
Makefile:
	@echo


target %: argv = $(subst ., ,$@)
target %: module = $(word 1, $(argv))
target %: method = $(word 2, $(argv))
%: reset
	PYTHONPATH="./:../" poetry run coverage run --branch --source=../django_client_framework ./manage.py test --no-input -v2 -p "$(module).py" -k "$(method)"
	poetry run coverage xml
