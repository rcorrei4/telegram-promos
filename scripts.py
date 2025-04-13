import asyncio
import os

from dotenv import load_dotenv
from telethon.sync import TelegramClient

from db.db import (
    add_product,
    add_whitelisted_channel,
    delete_product,
    delete_whitelisted_channel,
    list_products,
    list_whitelisted_channels,
)

load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
client = TelegramClient("session_name", api_id, api_hash)

def show_main_menu():
    print("\n=== Product & Channel Tracker ===")
    print("1. Add a new product")
    print("2. View registered products")
    print("3. Delete a product by id")
    print("4. Add whitelisted channel")
    print("5. View whitelisted channels")
    print("6. Delete whitelisted channel")
    print("7. List all Telegram channels I'm in")
    print("0. Exit")
    return input("Choose an option: ").strip()

def handle_add_product():
    product = input("Enter the name of the product you want to keep track of: ").strip()
    if product:
        add_product(product)
        print(f"✅ '{product}' added to the watchlist.")
    else:
        print("⚠️ Product name cannot be empty.")

def handle_view_products():
    products = list_products()
    if products:
        print("\n📦 Watched Products:")
        for p in products:
            print(f"- {p[0]} (ID: {p[1]})")
    else:
        print("📭 No products registered yet.")

def handle_delete_product():
    product_id = input("Enter the id of the product you want to delete: ").strip()
    if product_id.isdigit():
        deleted_product = delete_product(int(product_id))
        if deleted_product:
            print(f"✅ '{deleted_product}' deleted successfully.")
        else:
            print("⚠️ Product not found.")
    else:
        print("❌ Invalid ID.")

def handle_add_channel():
    channel_id = input("Enter the channel ID to whitelist: ").strip()
    if channel_id.isdigit():
        add_whitelisted_channel(int(channel_id))
        print(f"✅ Channel {channel_id} added to whitelist.")
    else:
        print("❌ Invalid ID.")

def handle_view_channels():
    channels = list_whitelisted_channels()
    if channels:
        print("\n✅ Whitelisted Channels:")
        for cid in channels:
            print(f"- {cid}")
    else:
        print("📭 No whitelisted channels yet.")

def handle_delete_channel():
    channel_id = input("Enter the channel ID to remove: ").strip()
    if channel_id.isdigit():
        delete_whitelisted_channel(int(channel_id))
        print(f"❌ Channel {channel_id} removed from whitelist.")
    else:
        print("❌ Invalid ID.")

async def handle_list_telegram_channels():
    await client.start()
    dialogs = await client.get_dialogs()
    whitelisted = list_whitelisted_channels()
    
    print("\n📢 Telegram Channels You’re In:")
    for dialog in dialogs:
        entity = dialog.entity
        if hasattr(entity, 'megagroup') or hasattr(entity, 'broadcast'):
            name = getattr(entity, "title", "No Title")
            cid = entity.id
            mark = "✅" if cid in whitelisted else "❌"
            print(f"{mark} [{cid}] {name}")

def main():
    while True:
        choice = show_main_menu()

        match choice:
            case "1":
                handle_add_product()
            case "2":
                handle_view_products()
            case "3":
                handle_delete_product()
            case "4":
                handle_add_channel()
            case "5":
                handle_view_channels()
            case "6":
                handle_delete_channel()
            case "7":
                asyncio.run(handle_list_telegram_channels())
            case "0":
                print("👋 Exiting. Bye!")
                break
            case _:
                print("❌ Invalid option. Please choose a valid number.")

if __name__ == "__main__":
    main()
