cd /doc-src
make clean
nginx -g "daemon off;" &
while sleep 0.1; do
    find source | entr -n -d sh -c "make html && echo Running on http://localhost:12800"
done
wait
