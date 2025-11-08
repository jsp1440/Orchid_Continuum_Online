#!/usr/bin/env python3
"""
Deployment Configuration for Reserved VM
Runs 16 workers (complementing Julius's 32 when he comes online)
"""
import os

# Configuration for Reserved VM deployment
RESERVED_VM_CONFIG = {
    'TARGET_WORKERS': 16,  # Reserved VM runs 16 workers
    'WORKER_PREFIX': 'rv',  # Prefix: rv-1, rv-2, etc.
    'RUN_SEEDER': True,  # Reserved VM runs the ONLY seeder
    'CHECK_INTERVAL': 60,  # Check every 60 seconds
    'MIN_QUEUE_DEPTH': 1000,
    'LAUNCHER_SCRIPT': 'launcher_vm.sh'  # VM-specific launcher
}

# When Julius comes online, his config will be:
JULIUS_CONFIG = {
    'TARGET_WORKERS': 32,  # Julius runs 32 workers
    'WORKER_PREFIX': 'julius',  # Prefix: julius-1, julius-2, etc.
    'RUN_SEEDER': False,  # Julius does NOT run seeder (VM handles it)
    'LAUNCHER_SCRIPT': 'launcher.sh'
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('DEPLOYMENT_ENV', 'reserved_vm')
    
    if env == 'julius':
        return JULIUS_CONFIG
    else:
        return RESERVED_VM_CONFIG
