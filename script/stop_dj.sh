#!/bin/bash

BASE_DIR=$(cd "$(dirname "$0")/..";pwd)
cd $BASE_DIR

if [[ -f sqe_dj.pid ]]; then
    kill -9 `cat sqe_dj.pid`
    rm sqe_dj.pid
fi