docker stop trafficproject-container
docker system prune --force
docker build -t trafficprojectimg .
rem docker build --no-cache -t trafficprojectimg .
docker run --name trafficproject-container -p 8000:8000 --cpu-period=100000 --cpu-quota=100000 --memory=512m trafficprojectimg
rem docker run --name trafficproject-container -p 8000:8000 trafficprojectimg