start_process:
	docker build -t dart_test_server -f dart_test_server.dockerfile .
	docker build -t dart_test_app -f Dockerfile .
	docker run --name dart_python_server --network host --rm -it -d dart_test_server python manage.py runserver 
	docker run --network host -ti -v -d dart_test_app flutter test test/all_tests.dart
	docker stop dart_python_server
