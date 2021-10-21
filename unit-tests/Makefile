default: clean
	PYTHONPATH="./:../" poetry run coverage run --branch --source=../django_client_framework ./manage.py test --no-input -v2 -p "*.py"
	poetry run coverage xml

.PHONY: ci
ci: alpine-base
	docker-compose run --rm dcf-test-alpine ./manage.py test --no-input -v2 -p "*.py"

.PHONY: alpine-base
alpine-base:
	docker-compose build dcf-test-alpine

.PHONY: sh
sh: alpine-base
	docker-compose run --rm dcf-test-alpine sh

.PHONY: clean
clean:
	-cd dcf_test_app/migrations && rm -f 0001_initial.py
	PYTHONPATH="./:../" poetry run ./manage.py makemigrations

.PHONY: Makefile
Makefile:
	@echo


target %: argv = $(subst ., ,$@)
target %: module = $(word 1, $(argv))
target %: method = $(word 2, $(argv))
%: clean
	PYTHONPATH="./:../" poetry run coverage run --branch --source=../django_client_framework ./manage.py test --no-input -v2 -p "$(module).py" -k "$(method)"
	poetry run coverage xml
