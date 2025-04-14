import re
import sqlite3

from client_setup import client  # Need the client for get_entity and get_dialogs
from config import logger
from data_manager import get_whitelisted_channels, load_data
from db.db import add_whitelisted_channel, delete_whitelisted_channel


async def handle_add_channel(event, channel_id_str):
    """Handles the /add_channel command."""
    if not channel_id_str or not re.match(r"^-?\d+$", channel_id_str):
        await event.reply("❌ Usage: `/add_channel <channel_id>`")
        return
    try:
        channel_id = int(channel_id_str)
        channel_name = f"ID {channel_id}"
        try:
            if client and client.is_connected():
                 entity = await client.get_entity(channel_id)
                 channel_name = getattr(entity, 'title', channel_name)
            else:
                logger.warning("Client not connected, cannot fetch channel title during add.")
        except Exception as e:
            logger.warning(f"Could not fetch channel title for {channel_id}: {e}")
            await event.reply(f"⚠️ Warning: Could not verify channel {channel_id}. Added anyway.")

        add_whitelisted_channel(channel_id)
        load_data()
        await event.reply(f"✅ Channel '{channel_name}' (ID: `{channel_id}`) added to whitelist.")
        logger.info(f"Admin {event.sender_id} added channel: {channel_id}")
    except sqlite3.IntegrityError:
         await event.reply(f"⚠️ Channel ID `{channel_id}` is already whitelisted.")
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        await event.reply(f"⚠️ Error adding channel: {e}")

async def handle_list_channels(event):
    """Handles the /list_channels command."""
    try:
        from db.db import list_whitelisted_channels as list_raw_channels
        raw_channel_ids = list_raw_channels()
    except Exception as e:
        logger.error(f"Failed to fetch raw channel list for display: {e}")
        await event.reply("⚠️ Error fetching channel list details.")
        return

    if not raw_channel_ids:
        await event.reply("📭 No channels whitelisted.")
        return

    message = "✅ Whitelisted Channels (Raw IDs):\n"
    channels_to_list = list(raw_channel_ids)

    if not client or not client.is_connected():
        logger.warning("Client not connected, cannot fetch channel titles for list.")
        for channel_id in channels_to_list:
             message += f"- `{channel_id}`: (Name unavailable - client disconnected)\n"
    else:
        for channel_id in channels_to_list:
            name = f"ID {channel_id}"
            try:
                entity = await client.get_entity(channel_id)
                name = getattr(entity, 'title', name)
            except Exception as e:
                logger.warning(f"Could not fetch title for channel {channel_id} during list: {e}")
                pass
            message += f"- `{channel_id}`: {name}\n"

    await event.reply(message)
    logger.info(f"Admin {event.sender_id} listed channels.")


async def handle_del_channel(event, channel_id_str):
    """Handles the /del_channel command."""
    if not channel_id_str or not re.match(r"^-?\d+$", channel_id_str):
        await event.reply("❌ Usage: `/del_channel <channel_id>`")
        return
    try:
        channel_id = int(channel_id_str)
        delete_whitelisted_channel(channel_id)
        load_data()
        await event.reply(f"✅ Channel ID `{channel_id}` removed from whitelist (if it existed).")
        logger.info(f"Admin {event.sender_id} deleted channel: {channel_id}")
    except Exception as e:
        logger.error(f"Error deleting channel: {e}")
        await event.reply(f"⚠️ Error deleting channel: {e}")

async def handle_list_my_channels(event):
    """Handles the /list_my_channels command."""
    if not client or not client.is_connected():
        await event.reply("⚠️ Client is not connected. Cannot fetch channel list.")
        logger.warning("Attempted /list_my_channels while client disconnected.")
        return

    try:
        await event.reply("🔄 Fetching the UserBot's channel list...")
        my_channels_output = []
        dialogs = await client.get_dialogs(limit=None)

        normalized_whitelist = get_whitelisted_channels()
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
            if len(current_msg) + len(line) + 1 > 4090: # Telegram message length limit
                await event.reply(current_msg)
                current_msg = ""
            current_msg += line + "\n"
        # Send the last part
        if current_msg:
            await event.reply(current_msg)

        logger.info(f"Admin {event.sender_id} listed UserBot's channels.")

    except Exception as e:
        logger.error(f"Error handling /list_my_channels: {e}")
        await event.reply(f"⚠️ Error fetching channel list: {e}")