from telethon import TelegramClient

from config import API_HASH, API_ID, logger

# Initialize the Telegram client
# The session name 'session_name' will create a session_name.session file
# This file stores authorization keys and should be kept secure
try:
    client = TelegramClient('session_name', API_ID, API_HASH)
    logger.info("✅ Telegram client initialized.")
except Exception as e:
    logger.error(f"🛑 Failed to initialize Telegram client: {e}")
    client = None

async def connect_client():
    """Connects the client and checks authorization."""
    if not client:
        logger.error("🛑 Client not initialized, cannot connect.")
        return False

    try:
        logger.info("🔗 Connecting Telegram client...")
        await client.connect()
        if not await client.is_user_authorized():
            logger.error("⚠️ Client not authorized. Please run interactively once to login.")
            await client.disconnect()
            return False
        me = await client.get_me()
        logger.info(f"✅ Logged in as UserBot: {me.first_name} (ID: {me.id})")
        return True
    except Exception as e:
        logger.error(f"🛑 Error connecting or authorizing client: {e}")
        if client.is_connected():
            await client.disconnect()
        return False

async def disconnect_client():
    """Disconnects the client if connected."""
    if client and client.is_connected():
        logger.info("🔌 Disconnecting Telegram client...")
        await client.disconnect()
        logger.info("✅ Client disconnected.")