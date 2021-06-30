cd /doc-src
make clean
nginx -g "daemon off;" &
find source | entr sh -c "make html && echo Running at http://localhost:2111"
wait
