from config import logger
from db.db import list_products, list_whitelisted_channels

_wishlist = []
_whitelisted_channels = set()

def load_data():
    """Loads or reloads wishlist and whitelisted channels from the database."""
    global _wishlist, _whitelisted_channels
    logger.info("🔄 Loading data from database...")
    try:
        _wishlist = list_products()
        raw_channels = list_whitelisted_channels()
        _whitelisted_channels = set(cid[0] if isinstance(cid, tuple) else cid for cid in raw_channels)

        normalized_set = set()
        for cid in _whitelisted_channels:
             normalized_set.add(cid)
             if cid > 0:
                 normalized_set.add(int(f"-100{cid}"))
             elif str(cid).startswith("-100"):
                 normalized_set.add(int(str(cid)[4:]))
        _whitelisted_channels = normalized_set

        logger.info(f"🛒 Wishlist loaded: {len(_wishlist)} items.")
        logger.info(f"📢 Whitelist loaded: {len(_whitelisted_channels)} normalized channel IDs.")
    except Exception as e:
        logger.error(f"⚠️ Error loading data from DB: {e}")
        logger.error("Ensure products.db exists and db/initdb.py has been run.")
        _wishlist = []
        _whitelisted_channels = set()

def get_wishlist():
    """Returns the currently loaded wishlist."""
    return list(_wishlist)

def get_whitelisted_channels():
    """Returns the set of currently loaded and normalized whitelisted channel IDs."""
    return set(_whitelisted_channels)

def is_channel_whitelisted(channel_id):
    """Checks if a given channel ID is in the normalized whitelist."""
    return channel_id in _whitelisted_channels

load_data()