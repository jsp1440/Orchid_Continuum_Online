import os, subprocess, time, sys

DB = 'postgresql://neondb_owner:npg_feOt1Ek0KLrF@ep-snowy-firefly-afvebui7.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require'
TROPICOS = 'a7d4e354-8820-45f7-9c42-7d598b1804fd'
BHL = '077d1589-4e86-45e8-b3e2-e34410906bdb'
ENTRY = 'julius_multi_source_worker.py'  # change if needed

os.makedirs('logs', exist_ok=True)
procs = []
for i in range(1, 33):
    env = os.environ.copy()
    env['DATABASE_URL'] = DB
    env['TROPICOS_API_KEY'] = TROPICOS
    env['BHL_API_KEY'] = BHL
    env['WORKER_ID'] = 'julius-' + str(i)
    lf = open('logs/julius-' + str(i) + '.log', 'a')
    p = subprocess.Popen(['python3', ENTRY], stdout=lf, stderr=lf, env=env)
    procs.append((p, lf))
    print('started', 'julius-' + str(i), 'pid', p.pid)
    time.sleep(0.05)
print('launched', len(procs), 'workers')
