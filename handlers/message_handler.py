import re

from telethon import events
from telethon.errors import (
    ChannelPrivateError,
    ChatForwardsRestrictedError,
    ChatWriteForbiddenError,
    UserNotParticipantError,
)
from telethon.tl.types import PeerChannel, PeerChat

from client_setup import client  # Need client for forwarding
from commands.channel import (
    handle_add_channel,
    handle_del_channel,
    handle_list_channels,
    handle_list_my_channels,
)

# Import command handlers
from commands.product import (
    handle_add_product,
    handle_del_product,
    handle_list_products,
)
from config import ADMIN_USER_ID, TARGET_FORWARD_CHANNEL_ID, logger
from data_manager import get_wishlist, is_channel_whitelisted
from db.db import add_price_record  # Direct DB interaction for price recording
from utils import extract_price_from_text, is_multi_product_post


async def handle_help_command(event):
    """Handles the /help command."""
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

async def process_admin_command(event):
    """Parses and routes commands from the admin user."""
    text = event.raw_text
    if not text.startswith('/'):
        return # Ignore non-command messages from admin

    logger.info(f"⌨️ Received command from ADMIN ({event.sender_id}): {text}")
    command_parts = text.split(' ', 1)
    command = command_parts[0]
    args = command_parts[1].strip() if len(command_parts) > 1 else ""

    # Route command to the appropriate handler
    match command:
        case '/add_product':
            await handle_add_product(event, args)
        case '/list_products':
            await handle_list_products(event)
        case '/del_product':
            await handle_del_product(event, args)
        case '/add_channel':
            await handle_add_channel(event, args)
        case '/list_channels':
            await handle_list_channels(event)
        case '/del_channel':
            await handle_del_channel(event, args)
        case '/list_my_channels':
            await handle_list_my_channels(event)
        case '/help':
            await handle_help_command(event)
        case _:
            await event.reply("❌ Unknown command. Type `/help` for a list of commands.")


async def process_channel_message(event):
    """Processes messages from channels/groups for promotions."""
    channel_id = event.chat_id
    peer_id = event.message.peer_id
    resolved_id = None

    if isinstance(peer_id, PeerChannel):
        resolved_id = peer_id.channel_id
        # Apply the -100 prefix convention if necessary for matching
        if resolved_id > 0:
             resolved_id = int(f"-100{resolved_id}")
    elif isinstance(peer_id, PeerChat):
        resolved_id = peer_id.chat_id 
    else:
        return

    if not is_channel_whitelisted(resolved_id):
        return

    text = event.raw_text
    if not text:
        return

    logger.info(f"🔔 New message {event.id} from whitelisted source {resolved_id}...")

    # Skip posts likely containing multiple products
    if is_multi_product_post(text):
        logger.info(f"⏩ Skipping multi-product post from {resolved_id} (Msg ID: {event.id}).")
        return

    message_already_forwarded = False
    current_wishlist = get_wishlist() 

    for product_id, product_name in current_wishlist:
        if re.search(r'\b' + re.escape(product_name) + r'\b', text, re.IGNORECASE):
            price = extract_price_from_text(text)
            if price:
                logger.info(f"✅ Found '{product_name}' (ID: {product_id}) for R${price} in source {resolved_id} (Msg ID: {event.id})")
                try:
                    add_price_record(
                        product_id=product_id,
                        price=price,
                        currency="BRL", # Assuming BRL, could be made configurable
                        source_msg=text[:1000], # Limit source message length
                        channel=str(resolved_id)
                    )
                except Exception as e:
                    logger.error(f"⚠️ Failed to add price record for product {product_id}: {e}")

                if not message_already_forwarded and TARGET_FORWARD_CHANNEL_ID != 0:
                    if not client or not client.is_connected():
                         logger.error("🛑 Forwarding failed: Client is not connected.")
                         continue

                    try:
                        logger.info(f"▶️ Attempting to forward message {event.id} from {resolved_id} to {TARGET_FORWARD_CHANNEL_ID}...")
                        await client.forward_messages(
                            entity=TARGET_FORWARD_CHANNEL_ID,
                            messages=event.message,
                            from_peer=event.chat
                        )
                        logger.info(f" relayed message {event.id} successfully.")
                        message_already_forwarded = True
                    except (UserNotParticipantError, ChannelPrivateError):
                        logger.error(f"🛑 Forwarding failed: UserBot is not a participant in the target channel {TARGET_FORWARD_CHANNEL_ID} or channel is private.")
                    except ChatWriteForbiddenError:
                        logger.error(f"🛑 Forwarding failed: UserBot does not have permission to send messages in {TARGET_FORWARD_CHANNEL_ID}.")
                    except ChatForwardsRestrictedError:
                        logger.info(f"⚠️ Forwarding failed: UserBot cannot forward messages from {channel_id}. Coping the message instead...")
                        try:
                            await client.send_message(
                                entity=TARGET_FORWARD_CHANNEL_ID,
                                message=text
                            )
                            logger.info(f" relayed message {event.id} successfully.")
                            message_already_forwarded = True
                        except Exception as e:
                            logger.error(f"🛑 Forwarding message {event.id} failed with unexpected error: {e}")
                            logger.exception("Forwarding exception details:")
                    except Exception as e:
                        logger.error(f"🛑 Forwarding message {event.id} failed with unexpected error: {e}")
                        logger.exception("Forwarding exception details:")


                elif TARGET_FORWARD_CHANNEL_ID == 0:
                     if not message_already_forwarded:
                         logger.warning("⚠️ TARGET_FORWARD_CHANNEL_ID not set, skipping forward.")
                         message_already_forwarded = True

                # Once a product match is found and processed (incl. forwarding attempt), break the inner loop
                break
            else:
                logger.info(f"❓ Found '{product_name}' in {resolved_id} (Msg ID: {event.id}), but no price extracted.")



@events.register(events.NewMessage)
async def main_event_handler(event):
    """Main handler for all new messages."""
    # 1. Handle commands from Admin User in private chat
    if event.is_private and event.sender_id == ADMIN_USER_ID:
        await process_admin_command(event)
        return

    # 2. Handle messages from Channels and Groups
    if event.is_channel or event.is_group:
        await process_channel_message(event)
        return