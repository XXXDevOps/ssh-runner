#!/usr/bin/env bash


BASE_DIR=$(cd "$(dirname "$0")/..";pwd)
cd $BASE_DIR

if [[ -f sqe_dj.pid ]]; then
    kill -9 `cat sqe_dj.pid`
    rm sqe_dj.pid
fi

#source $BASE_DIR/conf/env.sh

source $BASE_DIR/bin/venv/bin/activate
nohup $BASE_DIR/bin/venv/bin/python3 $BASE_DIR/bin/davyJones.py  >/dev/null 2>&1 &


echo $! > sqe_dj.pid

#python $BASE_DIR/bin/health_check.py

echo 'Server is Running...'