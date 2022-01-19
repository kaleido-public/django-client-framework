# grep the project version

export DOC_VERSION=$(sed -n 's/version = "\(\d.\d\).*"/\1/p' < /pyproject.toml).x

cd /doc-src
nginx -g "daemon off;" &
while sleep 0.1; do
    find source | entr -n -d sh -c "echo DOC_VERSION=${DOC_VERSION} && \
        make -f sphinx.Makefile html && \
        echo Running on http://localhost:12800/${DOC_VERSION}/html/index.html"
done
wait
