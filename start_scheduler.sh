#!/bin/bash
sleep 6
curl -sk -X POST https://127.0.0.1:5000/scheduler/start \
  -H "Content-Type: application/json" \
  -d '{"validator_address": "38831f127211650b9e97933963d73e0c0c1b3e8925c3b879518fc9f2810beb30853aced49a5ec85675afe36ad5abd0343a5a095f5816e3c91a7e504283dd0f53"}'
