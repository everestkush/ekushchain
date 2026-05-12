#!/bin/bash
cd /home/kushal/everestkush
source venv/bin/activate
export EVERESTKUSH_MODE=api
export ROCKSDB_PATH=/home/kushal/everestkush/rocksdb_data
gunicorn -c gunicorn_config.py api:app
