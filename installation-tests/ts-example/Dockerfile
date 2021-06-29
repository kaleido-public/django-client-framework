FROM dcf-installation-tests-backend-example

RUN cp /_out/dcf-backend-example.tar.gz /dcf-backend-example.tar.gz
COPY ./clients/django-client-framework-typescript /django-client-framework-typescript
COPY ./installation-tests/ts-example/proj /proj
COPY ./installation-tests/ts-example/entrypoint.py /entrypoint.py

CMD python3 /entrypoint.py
