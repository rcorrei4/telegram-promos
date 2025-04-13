import logging
import os

from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')

ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0)) # User ID of the admin controlling the bot
TARGET_FORWARD_CHANNEL_ID = int(os.getenv('TARGET_FORWARD_CHANNEL_ID', 0)) # Channel ID to forward messages to

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if API_ID == 0 or not API_HASH:
    logger.error("🛑 API_ID and API_HASH must be set in the .env file.")
    exit(1)

if ADMIN_USER_ID == 0:
    logger.warning("⚠️ ADMIN_USER_ID is not set. Command handling via private message will be disabled.")
else:
    logger.info(f"🔑 Bot will accept commands from Admin User ID: {ADMIN_USER_ID}")

if TARGET_FORWARD_CHANNEL_ID == 0:
    logger.warning("⚠️ TARGET_FORWARD_CHANNEL_ID is not set. Message forwarding will be disabled.")
else:
    logger.info(f"📲 Bot will forward found promotions to Channel ID: {TARGET_FORWARD_CHANNEL_ID}")