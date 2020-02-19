#!/usr/bin/env sh
set -ex

python cli.py initialize --end 5000 --chunk 1000
nohup python cli.py monitor > monitor.log &
python cli.py merge
