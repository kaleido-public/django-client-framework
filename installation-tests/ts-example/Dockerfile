FROM dcf-installation-tests-backend-example

RUN cp /_out/dcf-backend-example.tar.gz /dcf-backend-example.tar.gz
COPY ./installation-tests/ts-example/proj /proj
COPY ./installation-tests/ts-example/entrypoint.py /entrypoint.py

CMD python3 /entrypoint.py
