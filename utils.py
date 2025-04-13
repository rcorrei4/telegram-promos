import re
from typing import Optional


def is_multi_product_post(text: str) -> bool:
    """Returns True if the message contains more than one price."""
    return len(re.findall(r"R\$\s*[\d.]+(?:,\d{2})?", text)) > 1

def extract_price_from_text(text: str) -> Optional[float]:
    """
    Extracts a price in BRL from a string, such as 'R$100', 'R$ 100.00', 'R$ 100,00'.
    Returns the price as a float (using '.' as decimal separator), or None if not found.
    """
    # Match R$ with optional space and either . or , as decimal separator
    match = re.search(r"R\$\s*([\d.]+,\d{2}|\d+(?:\.\d{2})?)", text)
    if match:
        raw_price = match.group(1)

        # Convert Brazilian format to float
        if "," in raw_price:
            raw_price = raw_price.replace(".", "").replace(",", ".")
        return float(raw_price)

    return None