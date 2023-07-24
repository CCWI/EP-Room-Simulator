import subprocess
import sys

# this python script installs the software on the computer. It validates if no venv is currently set in the
# executing shell/cmd. If so, a full installation is done. Venv is created and activated, packages get installed
# the mongodb docker image gets pulled and backend and frontend getting started

# if the executing shell is already in the created venv, then just the docker container, backend and frontend
# is started

if sys.prefix == sys.base_prefix:
    print("Venv not created. Initiating fresh installation...")
    subprocess.run("installation.bat", shell=True)
    subprocess.Popen(["run_frontend.bat"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    subprocess.Popen(["run_spider.bat"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    subprocess.run("run_backend.bat", shell=True)
else:
    print("Installation already done, just starting the program...")
    subprocess.run("start_container.bat", shell=True)
    subprocess.Popen(["run_spider.bat"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    subprocess.Popen(["run_frontend.bat"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    subprocess.run("run_backend.bat", shell=True)
