FROM python:3

RUN mkdir /_work
WORKDIR /_work

COPY ./pyproject.toml           /_work/pyproject.toml
COPY ./README.md                /_work/README.md
COPY ./django_client_framework  /_work/django_client_framework
COPY ./unit-tests               /_work/unit-tests

RUN pip3 install /_work
ENV PYTHONPATH /_work

WORKDIR /_work/unit-tests
