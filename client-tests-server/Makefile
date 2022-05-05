default:
	cd ./migrations/ && git clean -xdi
	./manage.py makemigrations
	./manage.py migrate
	./manage.py test
