import asyncio

from client_setup import client, connect_client, disconnect_client
from config import ADMIN_USER_ID, TARGET_FORWARD_CHANNEL_ID, logger
from handlers.message_handler import main_event_handler


async def verify_target_channel():
    """Verifies access to the target forwarding channel if configured."""
    if TARGET_FORWARD_CHANNEL_ID != 0:
        if not client or not client.is_connected():
            logger.error("🛑 Cannot verify target channel: Client not connected.")
            return False
        try:
            await client.get_entity(TARGET_FORWARD_CHANNEL_ID)
            logger.info(f"✅ Successfully verified access to target channel {TARGET_FORWARD_CHANNEL_ID}.")
            return True
        except Exception as e:
             logger.error(f"🛑 Could not access target channel {TARGET_FORWARD_CHANNEL_ID}: {e}")
             logger.error("Please ensure the UserBot account is a member of the target channel and the ID is correct.")
             return False
    else:
        # No target channel configured, which is valid.
        return True

async def main():
    """Main function to initialize, connect, and run the bot."""
    logger.info("🚀 Initializing UserBot...")

    if not await connect_client():
        logger.error("🛑 Client connection failed. Exiting.")
        return

    if not await verify_target_channel():
        logger.warning("Continuing without guaranteed target channel access...")

    client.add_event_handler(main_event_handler)
    logger.info("✅ Event handler registered.")

    try:
        me = await client.get_me()
        my_user_id = me.id
        logger.info(f"🤖 Bot User ID: {my_user_id}")
        if ADMIN_USER_ID != 0:
            logger.info(f"👂 Send commands from Admin account ({ADMIN_USER_ID}) in private chat with UserBot ({my_user_id}).")
    except Exception as e:
        logger.error(f"⚠️ Could not get bot's own user info: {e}")


    logger.info("👂 Listening for messages...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 Ctrl+C received, shutting down...")
    finally:
        logger.info("🔌 Cleaning up...")
        if client and client.is_connected():
             loop.run_until_complete(disconnect_client())
        loop.close()
        logger.info("👋 Exited.")