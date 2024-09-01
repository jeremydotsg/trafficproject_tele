docker stop alpine
docker remove alpine
docker run -d --name alpine python:3.12.5-alpine3.20 /bin/sh -c "echo 'Hello World'; sleep infinity"
