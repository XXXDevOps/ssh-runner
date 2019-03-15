mkdir -p build/packages
mkdir -p dist
virtualenv -p /usr/local/bin/python3.6 ./build/venv
source ./build/venv/bin/activate
pip3 install -r requirements.txt
cp -r handlers ./build/packages/
cp -r connectors ./build/packages/
cp -r webshell ./build/packages/
cp -r templates ./build/packages/
