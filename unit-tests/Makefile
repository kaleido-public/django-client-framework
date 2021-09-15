default:
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

%:
	PYTHONPATH="./:../" poetry run coverage run --branch --source=../django_client_framework ./manage.py test --no-input -v2 -p "$@.py"
	poetry run coverage xml
