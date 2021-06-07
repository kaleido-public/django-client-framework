start_process:
	cd ../../; docker build -t dart_test_server -f installation-tests/dcf_dart_test/dart_server.dockerfile .; docker build -t dart_test_app -f installation-tests/dcf_dart_test/Dockerfile .;
	docker run --name dart_python_server --network host --rm -d dart_test_server python manage.py runserver 
	docker run --network host -v -d dart_test_app flutter test test/all_tests.dart
	docker stop dart_python_server
