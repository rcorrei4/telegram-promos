import sqlite3

DB_PATH = "products.db"

def add_product(name: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO watched_products (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    print(f"Product '{name}' added.")

def list_products():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM watched_products")
    products = cursor.fetchall()
    conn.close()
    return products

def delete_product(id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM watched_products WHERE id = ?", (id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return None

    product_name = row[0]
    cursor.execute("DELETE FROM watched_products WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return product_name

def add_price_record(product_id: int, price: float, currency: str, source_msg: str, channel: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO price_history (product_id, price, currency, source_msg, channel)
        VALUES (?, ?, ?, ?, ?)
    """, (product_id, price, currency, source_msg, channel))
    conn.commit()
    conn.close()
    print(f"Price {price} {currency} for product {product_id} added.")

def add_whitelisted_channel(channel_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO whitelisted_channels (channel_id) VALUES (?)", (channel_id,))
    conn.commit()
    conn.close()
    print(f"Channel (ID: {channel_id}) added to whitelist.")

def delete_whitelisted_channel(channel_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM whitelisted_channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()
    print(f"Channel ID {channel_id} removed from whitelist.")

def list_whitelisted_channels():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT channel_id FROM whitelisted_channels")
    channels = cursor.fetchall()
    conn.close()

    output = [row[0] for row in channels]
    return output
