import os
from core.rocksdb_storage import rocksdb_storage

BACKEND = os.environ.get('EKUSH_STORAGE_BACKEND', 'sqlite')

if BACKEND == 'rocksdb':
    storage = rocksdb_storage
    print(f"Using RocksDB storage backend")
else:
    storage = None
    print(f"Using SQLite storage backend")
