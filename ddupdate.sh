#!/bin/bash
set -x
here=$(readlink -fn $(dirname $0))
cd $here
PYTHONPATH=$PWD/src/ddupdate python3 -m src.ddupdate.main $@
