import asyncio
import logging
import os
import re
import sqlite3

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import (
    ChannelPrivateError,
    ChatWriteForbiddenError,
    UserNotParticipantError,
)
from telethon.tl.types import PeerChannel, PeerChat

from db.db import (
    add_price_record,
    add_product,
    add_whitelisted_channel,
    delete_product,
    delete_whitelisted_channel,
    list_products,
    list_whitelisted_channels,
)
from utils import extract_price_from_text, is_multi_product_post

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0)) # Default 0 if not set

TARGET_FORWARD_CHANNEL_ID = int(os.getenv('TARGET_FORWARD_CHANNEL_ID', 0)) # Default 0 if not set

client = TelegramClient('session_name', API_ID, API_HASH)

wishlist = []
WHITELISTED_CHANNEL_IDS = []
MY_USER_ID = None

def load_data_from_db():
    global wishlist, WHITELISTED_CHANNEL_IDS
    logger.info("🔄 Reloading data from database...")
    try:
        wishlist = list_products()
        WHITELISTED_CHANNEL_IDS = list_whitelisted_channels()
        logger.info(f"🛒 Wishlist loaded: {len(wishlist)} items.")
        logger.info(f"📢 Whitelist loaded: {len(WHITELISTED_CHANNEL_IDS)} channels.")
    except Exception as e:
        logger.error(f"⚠️ Error loading data from DB: {e}")
        logger.error("Ensure products.db exists and init_db.py has been run.")
        wishlist = []
        WHITELISTED_CHANNEL_IDS = []

async def handle_add_product_command(event, name):
    if not name:
        await event.reply("❌ Usage: `/add_product <product name>`")
        return
    try:
        add_product(name)
        load_data_from_db() # Reload
        await event.reply(f"✅ Product '{name}' added.")
        logger.info(f"Admin {event.sender_id} added product: {name}")
    except Exception as e:
        logger.error(f"Error adding product: {e}")
        await event.reply(f"⚠️ Error adding product: {e}")

async def handle_list_products_command(event):
    if not wishlist:
        await event.reply("📭 No products watched.")
        return
    message = "📦 Watched Products:\n" + "\n".join([f"- `{pid}`: {pname}" for pid, pname in wishlist])
    await event.reply(message)
    logger.info(f"Admin {event.sender_id} listed products.")

async def handle_del_product_command(event, product_id_str):
    if not product_id_str or not product_id_str.isdigit():
        await event.reply("❌ Usage: `/del_product <product_id>`")
        return
    try:
        product_id = int(product_id_str)
        deleted_product_name = delete_product(product_id)
        if deleted_product_name:
            load_data_from_db()
            await event.reply(f"✅ Product '{deleted_product_name}' (ID: {product_id}) deleted.")
            logger.info(f"Admin {event.sender_id} deleted product ID: {product_id}")
        else:
            await event.reply(f"⚠️ Product ID `{product_id}` not found.")
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        await event.reply(f"⚠️ Error deleting product: {e}")

async def handle_add_channel_command(event, channel_id_str):
    if not channel_id_str or not re.match(r"^-?\d+$", channel_id_str):
        await event.reply("❌ Usage: `/add_channel <channel_id>`")
        return
    try:
        channel_id = int(channel_id_str)
        channel_name = f"ID {channel_id}"
        try:
            entity = await client.get_entity(channel_id)
            channel_name = getattr(entity, 'title', channel_name)
        except Exception:
            await event.reply(f"⚠️ Warning: Could not verify channel {channel_id}. Added anyway.")

        add_whitelisted_channel(channel_id)
        load_data_from_db()
        await event.reply(f"✅ Channel '{channel_name}' (ID: `{channel_id}`) added to whitelist.")
        logger.info(f"Admin {event.sender_id} added channel: {channel_id}")
    except sqlite3.IntegrityError:
         await event.reply(f"⚠️ Channel ID `{channel_id}` is already whitelisted.")
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        await event.reply(f"⚠️ Error adding channel: {e}")

async def handle_list_channels_command(event):
    if not WHITELISTED_CHANNEL_IDS:
        await event.reply("📭 No channels whitelisted.")
        return
    message = "✅ Whitelisted Channels:\n"
    channels_to_list = list(WHITELISTED_CHANNEL_IDS)
    for channel_id in channels_to_list:
        name = f"ID {channel_id}"
        try:
            entity = await client.get_entity(channel_id)
            name = getattr(entity, 'title', name)
        except Exception: 
            pass
        message += f"- `{channel_id}`: {name}\n"
    await event.reply(message)
    logger.info(f"Admin {event.sender_id} listed channels.")

async def handle_del_channel_command(event, channel_id_str):
    if not channel_id_str or not re.match(r"^-?\d+$", channel_id_str):
        await event.reply("❌ Usage: `/del_channel <channel_id>`")
        return
    try:
        channel_id = int(channel_id_str)
        delete_whitelisted_channel(channel_id)
        load_data_from_db() # Reload
        await event.reply(f"✅ Channel ID `{channel_id}` removed from whitelist (if it existed).")
        logger.info(f"Admin {event.sender_id} deleted channel: {channel_id}")
    except Exception as e:
        logger.error(f"Error deleting channel: {e}")
        await event.reply(f"⚠️ Error deleting channel: {e}")

async def handle_list_my_channels_command(event):
    """Handles the /list_my_channels command sent FROM THE ADMIN ACCOUNT."""
    try:
        await event.reply("🔄 Fetching the UserBot's channel list...")
        my_channels_output = []
        dialogs = await client.get_dialogs(limit=None)

        normalized_whitelist = set()
        for cid in WHITELISTED_CHANNEL_IDS:
             normalized_whitelist.add(cid)
             if cid > 0: 
                 normalized_whitelist.add(int(f"-100{cid}"))
             elif str(cid).startswith("-100"): 
                 normalized_whitelist.add(int(str(cid)[4:]))

        count = 0
        for dialog in dialogs:
            if dialog.is_channel:
                entity = dialog.entity
                is_broadcast = getattr(entity, 'broadcast', False)
                is_megagroup = getattr(entity, 'megagroup', False)
                if is_broadcast and not is_megagroup:
                    channel_id = entity.id
                    full_channel_id = int(f"-100{channel_id}") if channel_id > 0 else channel_id
                    title = getattr(entity, 'title', 'Unknown Channel')
                    is_whitelisted = full_channel_id in normalized_whitelist or channel_id in normalized_whitelist
                    mark = "✅" if is_whitelisted else "❌"
                    my_channels_output.append(f"{mark} `{full_channel_id}`: {title}")
                    count += 1

        if not my_channels_output:
            await event.reply("🤷 The UserBot account isn't in any broadcast channels.")
            return

        response = f"📢 UserBot account is in {count} broadcast channels:\n\n"
        current_msg = response
        for line in my_channels_output:
            if len(current_msg) + len(line) + 1 > 4090:
                await event.reply(current_msg)
                current_msg = ""
            current_msg += line + "\n"
        await event.reply(current_msg)
        logger.info(f"Admin {event.sender_id} listed UserBot's channels.")

    except Exception as e:
        logger.error(f"Error handling /list_my_channels: {e}")
        await event.reply(f"⚠️ Error fetching channel list: {e}")

async def handle_help_command(event):
    help_text = """
    **🤖 UserBot Commands (Send from Admin Account)**

    **Products:**
    `/add_product <name>`
    `/list_products`
    `/del_product <id>`

    **Channels:**
    `/add_channel <id>`
    `/list_channels`
    `/del_channel <id>`

    **UserBot Account Info:**
    `/list_my_channels` - List channels the UserBot is in.

    `/help` - Shows this message.
    """
    await event.reply(help_text, parse_mode='md')



@client.on(events.NewMessage)
async def handle_new_message(event):
    if event.is_private and event.sender_id == ADMIN_USER_ID:
        text = event.raw_text
        if text.startswith('/'):
            logger.info(f"⌨️ Received command from ADMIN ({event.sender_id}): {text}")
            command_parts = text.split(' ', 1)
            command = command_parts[0]
            args = command_parts[1].strip() if len(command_parts) > 1 else ""

            match command:
                case '/add_product':
                    await handle_add_product_command(event, args)
                case '/list_products':
                    await handle_list_products_command(event)
                case '/del_product':
                    await handle_del_product_command(event, args)
                case '/add_channel':
                    await handle_add_channel_command(event, args)
                case '/list_channels':
                    await handle_list_channels_command(event)
                case '/del_channel':
                    await handle_del_channel_command(event, args)
                case '/list_my_channels':
                    await handle_list_my_channels_command(event)
                case '/help':
                    await handle_help_command(event)
                case _:
                    await event.reply("❌ Unknown command. Type `/help` for a list of commands.")

    # --- Price Tracking and Forwarding Logic ---
    if event.is_channel or event.is_group:
        channel_id = event.chat_id
        peer_id = event.message.peer_id
        resolved_id = None
        if isinstance(peer_id, PeerChannel): 
            resolved_id = peer_id.channel_id
        elif isinstance(peer_id, PeerChat): 
            resolved_id = peer_id.chat_id

        if resolved_id:
            normalized_whitelist = set()
            for cid in WHITELISTED_CHANNEL_IDS:
                normalized_whitelist.add(cid)
                if cid > 0: 
                    normalized_whitelist.add(int(f"-100{cid}"))
                elif str(cid).startswith("-100"): 
                    normalized_whitelist.add(int(str(cid)[4:]))

            is_whitelisted = resolved_id in normalized_whitelist or channel_id in normalized_whitelist

            if not is_whitelisted: 
                return

            text = event.raw_text
            if not text: 
                return

            logger.info(f"🔔 New message {event.id} from whitelisted channel {resolved_id}...")

            if is_multi_product_post(text):
                logger.info("⏩ Skipping multi-product post.")
                return

            message_already_forwarded = False
            current_wishlist = list(wishlist)

            for product_id, product_name in current_wishlist:
                if re.search(r'\b' + re.escape(product_name) + r'\b', text, re.IGNORECASE):
                    price = extract_price_from_text(text)
                    if price:
                        logger.info(f"✅ Found '{product_name}' (ID: {product_id}) for R${price} in channel {resolved_id}")
                        add_price_record(
                            product_id=product_id,
                            price=price,
                            currency="BRL",
                            source_msg=text[:1000],
                            channel=str(resolved_id)
                        )

                        if not message_already_forwarded and TARGET_FORWARD_CHANNEL_ID != 0:
                            try:
                                logger.info(f"▶️ Attempting to forward message {event.id} to {TARGET_FORWARD_CHANNEL_ID}...")
                                await client.forward_messages(
                                    entity=TARGET_FORWARD_CHANNEL_ID,
                                    messages=event.message,
                                )
                                logger.info(f" relayed message {event.id} successfully.")
                                message_already_forwarded = True
                            except (UserNotParticipantError, ChannelPrivateError):
                                logger.error(f"🛑 Forwarding failed: UserBot is not a participant in the target channel {TARGET_FORWARD_CHANNEL_ID} or channel is private.")
                            except ChatWriteForbiddenError:
                                logger.error(f"🛑 Forwarding failed: UserBot does not have permission to send messages in {TARGET_FORWARD_CHANNEL_ID}.")
                            except Exception as e:
                                logger.error(f"🛑 Forwarding message {event.id} failed with unexpected error: {e}")
                        elif TARGET_FORWARD_CHANNEL_ID == 0:
                             logger.warning("⚠️ TARGET_FORWARD_CHANNEL_ID not set, skipping forward.")
                             message_already_forwarded = True

                        break

async def main():
    global MY_USER_ID
    logger.info("🚀 Initializing UserBot client...")

    if ADMIN_USER_ID == 0:
        logger.warning("⚠️ ADMIN_USER_ID is not set. Command handling via private message will be disabled.")
    else:
         logger.info(f"🔑 Bot will accept commands from Admin User ID: {ADMIN_USER_ID}")

    if TARGET_FORWARD_CHANNEL_ID == 0:
        logger.warning("⚠️ TARGET_FORWARD_CHANNEL_ID is not set in .env file. Message forwarding will be disabled.")
    else:
        logger.info(f"📲 Bot will forward found promotions to Channel ID: {TARGET_FORWARD_CHANNEL_ID}")

    await client.connect()
    if not await client.is_user_authorized():
        logger.error("⚠️ Client not authorized. Please run interactively once to login.")
        return

    me = await client.get_me()
    MY_USER_ID = me.id
    logger.info(f"✅ Logged in as UserBot: {me.first_name} (ID: {MY_USER_ID})")

    if TARGET_FORWARD_CHANNEL_ID != 0:
        try:
            await client.get_entity(TARGET_FORWARD_CHANNEL_ID)
            logger.info(f"✅ Successfully found target channel {TARGET_FORWARD_CHANNEL_ID}.")
        except Exception as e:
             logger.error(f"🛑 Could not access target channel {TARGET_FORWARD_CHANNEL_ID}: {e}")
             logger.error("Please ensure the UserBot account is a member of the target channel and the ID is correct.")

    load_data_from_db()

    logger.info("👂 Listening for messages...")
    if ADMIN_USER_ID != 0:
        logger.info(f"🤖 Send commands from Admin account ({ADMIN_USER_ID}) in private chat with UserBot ({MY_USER_ID}).")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down...")
    finally:
        logger.info("👋 Exited.")