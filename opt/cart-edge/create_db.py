import sqlite3
from pathlib import Path

base = Path('/opt/cart-edge')
db_path = base / 'db' / 'cart.db'
schema_path = base / 'schema.sql'

db_path.parent.mkdir(parents=True, exist_ok=True)
with open(schema_path) as f:
    schema = f.read()

conn = sqlite3.connect(db_path)
conn.executescript(schema)
conn.commit()
conn.close()
print(db_path)
