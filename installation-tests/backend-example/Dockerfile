FROM dcf-installation-tests-ubuntu-base

COPY . /django_client_framework
COPY ./installation-tests/backend-example/entrypoint.py /entrypoint.py
COPY ./installation-tests/backend-example/overwrite /_overwrite
RUN pip3 install /django_client_framework

RUN mkdir /_out
RUN python3 /entrypoint.py
