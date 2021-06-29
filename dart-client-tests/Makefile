start_process:
	docker-compose build
	docker-compose run --rm -d dart_test_server
	docker-compose run --rm dart_test_app
	docker-compose down
