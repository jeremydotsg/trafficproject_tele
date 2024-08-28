docker stop trafficproject-container
docker system prune --force
rem docker build -t trafficprojectimg .
docker build --no-cache -t trafficprojectimg .
docker run --name trafficproject-container -p 8000:8000 trafficprojectimg
