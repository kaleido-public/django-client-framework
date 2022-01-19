default:
	docker compose up --build --force-recreate -V

ci:
	docker compose run --rm -w /doc-src server \
		make -f sphinx.Makefile html
