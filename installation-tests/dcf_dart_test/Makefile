start_process:
	cd ../../; docker build -t dart_test_server -f installation-tests/dcf_dart_test/dart_server.dockerfile . --no-cache; docker build -t dart_test_app -f installation-tests/dcf_dart_test/Dockerfile . --no-cache;
	docker run --name dart_python_server --network host --rm -it -d dart_test_server python manage.py runserver 
	docker run --network host -ti -v -d dart_test_app flutter test test/all_tests.dart
	docker stop dart_python_server
