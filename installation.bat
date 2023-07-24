@echo off

title Installation
echo creating and activating venv...
python -m venv venv
call .\venv/Scripts/activate.bat
echo ...done

echo install requirements...
pip install -r requirements.txt
echo ...done

echo pulling and starting mongodb docker image...
docker pull "mongo:6.0.2"
docker run --name simulation_db -p 27017:27017 -d mongo:6.0.2
echo ...done
