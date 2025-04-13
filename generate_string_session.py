# generate_string_session.py
import os

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')

print("Generating string session...")
# Using ':memory:' prevents creating a local file
with TelegramClient(StringSession(), api_id, api_hash) as client:
    print(client.session.save())