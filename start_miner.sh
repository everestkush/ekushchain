#!/bin/bash
cd /home/kushal/everestkush
source venv/bin/activate
export EVERESTKUSH_MODE=miner
export ROCKSDB_PATH=/home/kushal/everestkush/rocksdb_data
python3 fixed_miner.py
