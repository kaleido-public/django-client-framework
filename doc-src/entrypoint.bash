cd /doc-src
make clean
nginx -g "daemon off;" &
find source | entr -n sh -c "make html && echo Running at http://localhost:12800"

wait
