import re

def parse_llm_response(text: str) -> dict:
    """
    Robust medicine info parser — works even with missing or inconsistent keys.
    """
    if not text or not isinstance(text, str):
        return {
            'Branded_Name': 'Unknown',
            'Generic_Name': '',
            'Company': '',
            'Price': '',
            'Description': '',
            'Batch': '',
            'Barcode': '',
            'Barcodes': ''
        }

    parsed = {}
    for line in text.splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            parsed[k.strip().lower()] = v.strip()

    def find_key(*keys):
        for k in keys:
            if k in parsed:
                return parsed[k]
        return ''

    # Extract a numeric price
    price_text = find_key('price per tablet (approx)', 'price', 'approx price')
    price_match = re.search(r'(\d+(?:\.\d+)?)', price_text)
    price_value = price_match.group(1) if price_match else price_text.replace('₹', '').strip()

    # Build dictionary safely — even if missing keys
    row = {
        'Branded_Name': find_key('branded name', 'branded_name', 'brand name', 'name') or 'Unknown',
        'Generic_Name': find_key('generic', 'generic_name') or '',
        'Company': find_key('company', 'manufacturer') or '',
        'Price': price_value or '',
        'Description': find_key('uses', 'description', 'purpose', 'use', 'application') or '',
        'Batch': '',
        'Barcode': '',
        'Barcodes': ''
    }

    # Always return a full dict — never fail on missing fields
    for key in ['Branded_Name', 'Generic_Name', 'Company', 'Price', 'Description', 'Batch', 'Barcode', 'Barcodes']:
        row.setdefault(key, '')

    return row


def is_llm_response(text: str) -> bool:
    if not text or text.strip().lower() in ('unknown', '', 'unknown medicine'):
        return False
    # detect if text resembles LLM output
    keywords = ['branded name', 'generic', 'company', 'price', 'uses']
    return any(k in text.lower() for k in keywords)
