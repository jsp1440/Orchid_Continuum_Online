#!/usr/bin/env python3
import subprocess
import time
import os

print("Starting 4 stable workers...")

workers = []
for i in range(4):
    worker_id = f"stable-worker-{i+1}"
    cmd = ["python3", "-u", "julius_multi_source_worker.py", worker_id]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    workers.append((worker_id, proc))
    print(f"Started {worker_id} (PID: {proc.pid})")
    time.sleep(2)

print("\nWorkers running. Monitoring...")
time.sleep(10)

for worker_id, proc in workers:
    if proc.poll() is None:
        print(f"✅ {worker_id} is alive")
    else:
        print(f"❌ {worker_id} died")

print("\nPress Ctrl+C to stop")
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    print("\nStopping workers...")
    for worker_id, proc in workers:
        proc.terminate()
