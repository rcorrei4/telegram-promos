from config import logger
from data_manager import get_wishlist, load_data
from db.db import add_product, delete_product


async def handle_add_product(event, name):
    """Handles the /add_product command."""
    if not name:
        await event.reply("❌ Usage: `/add_product <product name>`")
        return
    try:
        add_product(name)
        load_data()
        await event.reply(f"✅ Product '{name}' added.")
        logger.info(f"Admin {event.sender_id} added product: {name}")
    except Exception as e:
        logger.error(f"Error adding product: {e}")
        await event.reply(f"⚠️ Error adding product: {e}")

async def handle_list_products(event):
    """Handles the /list_products command."""
    wishlist = get_wishlist()
    if not wishlist:
        await event.reply("📭 No products watched.")
        return
    message = "📦 Watched Products:\n" + "\n".join([f"- `{pid}`: {pname}" for pid, pname in wishlist])
    await event.reply(message)
    logger.info(f"Admin {event.sender_id} listed products.")

async def handle_del_product(event, product_id_str):
    """Handles the /del_product command."""
    if not product_id_str or not product_id_str.isdigit():
        await event.reply("❌ Usage: `/del_product <product_id>`")
        return
    try:
        product_id = int(product_id_str)
        deleted_product_name = delete_product(product_id)
        if deleted_product_name:
            load_data()
            await event.reply(f"✅ Product '{deleted_product_name}' (ID: {product_id}) deleted.")
            logger.info(f"Admin {event.sender_id} deleted product ID: {product_id}")
        else:
            await event.reply(f"⚠️ Product ID `{product_id}` not found.")
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        await event.reply(f"⚠️ Error deleting product: {e}")