#!/bin/bash
cd /home/kushal/everestkush
source venv/bin/activate
export FLASK_ENV=production
export FLASK_DEBUG=0

# Start scheduler in background after node is ready
(sleep 8 && curl -sk -X POST https://127.0.0.1:5000/scheduler/start \
  -H "Content-Type: application/json" \
  -d '{"validator_address": "38831f127211650b9e97933963d73e0c0c1b3e8925c3b879518fc9f2810beb30853aced49a5ec85675afe36ad5abd0343a5a095f5816e3c91a7e504283dd0f53"}') &

exec gunicorn --bind 192.168.23.5:5000 --workers 1 --threads 4 --timeout 120 --certfile=cert.pem --keyfile=key.pem api:app
