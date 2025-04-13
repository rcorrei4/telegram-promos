# init_db.py
import sqlite3

conn = sqlite3.connect("products.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS watched_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    price REAL,
    currency TEXT,
    source_msg TEXT,
    channel TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(product_id) REFERENCES watched_products(id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS whitelisted_channels (
    channel_id INTEGER PRIMARY KEY
)
''')

conn.commit()
conn.close()
print("Database initialized!")
