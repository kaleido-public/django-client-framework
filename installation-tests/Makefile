.PHONY: all
all: backend-example ts-example

.PHONY: ubuntu-base
ubuntu-base:
	docker-compose build dcf-installation-tests-ubuntu-base


.PHONY: example
backend-example: ubuntu-base
	docker-compose build backend-example

.PHONY: ts-example
ts-example: backend-example
	docker-compose build ts-example
	docker-compose run --rm ts-example
