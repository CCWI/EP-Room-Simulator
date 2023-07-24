#!/bin/bash
echo creating and activating venv...
python3 -m venv venv
# under Windows, venv is created in Scripts folder. Posix users should change /Scripts to /bin
source venv/bin/activate
echo ...done

echo install requirements...
pip install --require-virtualenv -r requirements.txt
echo ...done

echo pulling and starting mongodb docker image...
sudo docker pull "mongo:6.0.2"
sudo docker run --name simulation_db -p 27017:27017 -d mongo:6.0.2
echo ...done
