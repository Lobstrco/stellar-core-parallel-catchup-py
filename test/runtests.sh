#!/usr/bin/env bash
set -ex

isort . --recursive --check-only
flake8 .

python cli.py initialize --end 1000 --chunk 100
python cli.py monitor
python cli.py merge

# todo: check results with stellar-core
